"""
tasks.py — Sistema de colas y tareas en segundo plano para Jarvis usando Celery.
Permite ejecutar procesos pesados (RAG, Scraping, Inferencias largas) sin bloquear la interfaz.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
from celery import Celery
import json
import traceback

# Configuración de Celery apuntando a Redis local (asegúrate de tener Memurai o Redis en WSL)
app = Celery(
    'jarvis_tasks', 
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Configuraciones adicionales de potencia
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600, # 1 hora máxima por tarea para evitar bloqueos
)

@app.task(bind=True, max_retries=3)
def query_ollama_async(self, prompt: str, model: str = 'qwen2.5-coder:7b'):
    """Ejecuta una consulta asíncrona a Ollama usando LangChain."""
    try:
        from langchain_community.chat_models import ChatOllama
        from langchain.schema import HumanMessage

        llm = ChatOllama(model=model, base_url="http://localhost:11434")
        response = llm.invoke([HumanMessage(content=prompt)])
        return {"status": "success", "result": response.content}
    except Exception as exc:
        # Reintentar si falla la conexión a Ollama
        raise self.retry(exc=exc, countdown=10)


@app.task(bind=True)
def background_rag_index(self):
    """Reconstruye el índice de ChromaDB en segundo plano."""
    try:
        # Importamos la lógica existente de ingesta
        # Agregamos path al sys para que resuelva los imports locales
        from pathlib import Path
        import sys
        sys.path.append(str(Path(__file__).parent.parent))
        
        from src.rag.ingest import ingest
        
        # Ejecutamos la ingesta completa
        ingest()
        return {"status": "success", "message": "Base de datos ChromaDB actualizada correctamente."}
    except Exception as e:
        error_msg = str(e)
        print(f"Error en RAG index task: {error_msg}")
        return {"status": "error", "error": error_msg, "trace": traceback.format_exc()}


@app.task(bind=True, max_retries=2)
def background_web_task(self, task_description: str):
    """Ejecuta una tarea de automatización web pesada en segundo plano."""
    try:
        from pathlib import Path
        import sys
        sys.path.append(str(Path(__file__).parent.parent))
        
        from src.tools.browser_agent import run_browser_task
        
        result = run_browser_task(task_description)
        return {"status": "success", "result": str(result)}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)

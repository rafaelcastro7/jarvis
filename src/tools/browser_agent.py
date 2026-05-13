"""
browser_agent.py — Herramienta de navegación web para Jarvis.
Utiliza 'browser-use' y 'langchain' para navegar, extraer datos y tomar acciones.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import asyncio
from langchain_community.chat_models import ChatOllama
from browser_use import Agent

def run_browser_task(task_description: str, headless: bool = False):
    """
    Inicia una tarea autónoma en el navegador usando qwen2.5-coder:7b.
    Nota: Qwen2.5 es bueno en código, lo que ayuda a interpretar el DOM.
    """
    print(f"🌐 Iniciando agente web para: '{task_description}'")
    
    # Configuramos el LLM local
    llm = ChatOllama(model="qwen2.5-coder:7b", base_url="http://localhost:11434")
    
    # Configuramos el agente
    agent = Agent(
        task=task_description,
        llm=llm,
        # Browser-use soporta configuración extra para usar Playwright existente
    )
    
    async def _run():
        result = await agent.run()
        return result

    # Ejecutar loop asíncrono
    try:
        final_result = asyncio.run(_run())
        print("\n✅ Tarea web completada.")
        return final_result
    except Exception as e:
        print(f"\n❌ Error en el agente web: {e}")
        return str(e)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python browser_agent.py \"Tarea a realizar en la web\"")
        sys.exit(1)
        
    task = " ".join(sys.argv[1:])
    result = run_browser_task(task)
    print("\n--- Resultado Final ---")
    print(result)

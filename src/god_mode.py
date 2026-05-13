"""
god_mode.py — Punto de entrada unificado para el Modo Dios de Jarvis.
Integra LangChain, RAG con ChromaDB, Navegación Autónoma y Visión.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

# Add parent directory to path so tools can be imported
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from langchain_community.chat_models import ChatOllama
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.memory import ConversationBufferMemory

# Import tools
from src.rag.chroma_store import search as rag_search
from src.tools.vision import analyze_image
from src.tools.browser_agent import run_browser_task

def get_god_mode_agent():
    """Configura el agente ReAct con todas las herramientas de Jarvis."""
    llm = ChatOllama(model="qwen2.5-coder:7b", base_url="http://localhost:11434")
    
    # 1. Herramienta RAG (Conocimiento Local con HyDE)
    def rag_tool(query: str) -> str:
        # Activamos HyDE para mejorar la recuperación semántica
        results = rag_search(query, top_k=3, use_hyde=True)
        if not results:
            return "No encontré información local sobre eso."
        return "\n\n".join([f"Fuente: {r['file']}\nContenido: {r['text']}" for r in results])

    # 2. Herramienta Visión (Imágenes)
    def vision_tool(args: str) -> str:
        # args expected: "path/to/image.jpg|prompt"
        parts = args.split("|")
        img_path = parts[0].strip()
        prompt = parts[1].strip() if len(parts) > 1 else "Describe the image"
        return analyze_image(img_path, prompt)

    # 3. Herramienta Navegador (Browser-Use)
    def browser_tool(task: str) -> str:
        # Importante: Esto toma control del navegador real
        return str(run_browser_task(task))

    tools = [
        Tool(
            name="Search_Local_Knowledge",
            func=rag_tool,
            description="Útil para buscar en los documentos locales y skills del usuario. Usa esto primero para consultas técnicas."
        ),
        Tool(
            name="Analyze_Image",
            func=vision_tool,
            description="Útil para analizar imágenes locales. La entrada debe ser 'ruta_de_la_imagen | pregunta_sobre_la_imagen'."
        ),
        Tool(
            name="Web_Browser",
            func=browser_tool,
            description="Útil para navegar por internet, buscar información actualizada o automatizar acciones en la web. La entrada es la tarea que debe realizar el navegador."
        )
    ]

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    agent = initialize_agent(
        tools, 
        llm, 
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory, 
        verbose=True,
        handle_parsing_errors=True
    )
    
    return agent

def main():
    print("==============================================")
    print("🤖 JARVIS GOD MODE ACTIVADO")
    print("==============================================")
    print("Herramientas disponibles: [RAG Local (ChromaDB), Visión (Moondream), Navegador Web (Browser-use)]")
    print("Escribe 'salir' para terminar.\n")
    
    agent = get_god_mode_agent()
    
    while True:
        try:
            user_input = input("Tú: ")
            if user_input.lower() in ["salir", "exit", "quit"]:
                break
                
            response = agent.run(user_input)
            print(f"\nJarvis: {response}\n")
            
        except KeyboardInterrupt:
            print("\nSaliendo...")
            break
        except Exception as e:
            print(f"\nError en Modo Dios: {e}\n")

if __name__ == "__main__":
    main()

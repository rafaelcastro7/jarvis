"""
browser_agent.py — Herramienta de navegación web para Jarvis.
Utiliza 'browser-use' y 'langchain' para navegar, extraer datos y tomar acciones.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import asyncio
from langchain_community.chat_models import ChatOllama
from browser_use import Agent, Controller

controller = Controller()

@controller.action("Take a screenshot of the current page and analyze it with local vision (Moondream2) to understand layout or find elements.")
async def analyze_screen_with_moondream(prompt: str, browser_context=None):
    """
    Action that captures the screen and sends it to the local Moondream model.
    """
    try:
        from pathlib import Path
        import sys
        sys.path.append(str(Path(__file__).parent.parent.parent))
        from src.tools.vision import analyze_image
        import uuid
        
        import tempfile
        import os
        from browser_use.browser.context import BrowserContext
        
        # Guard clause
        if browser_context is None:
            return "Error: browser_context is missing."
            
        # Tomar screenshot a través de Playwright
        page = await browser_context.get_current_page()
        
        temp_dir = tempfile.gettempdir()
        screenshot_path = os.path.join(temp_dir, f"jarvis_vision_{uuid.uuid4().hex}.jpg")
        
        await page.screenshot(path=screenshot_path, type="jpeg", quality=80)
        
        # Llamar a Moondream
        print(f"👁️ Analizando pantalla con Moondream: {prompt}")
        vision_result = analyze_image(screenshot_path, prompt)
        
        # Limpiar
        try:
            os.remove(screenshot_path)
        except:
            pass
            
        return f"Vision Analysis Result: {vision_result}"
    except Exception as e:
        return f"Error: {e}"

def run_browser_task(task_description: str, headless: bool = False):
    """
    Inicia una tarea autónoma en el navegador usando qwen2.5-coder:7b.
    Incorpora capacidades multimodales a través del controlador personalizado.
    """
    print(f"🌐 Iniciando agente web para: '{task_description}'")
    
    # Configuramos el LLM local
    llm = ChatOllama(model="qwen2.5-coder:7b", base_url="http://localhost:11434")
    
    # Configuramos el agente con el controlador
    agent = Agent(
        task=task_description,
        llm=llm,
        controller=controller
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

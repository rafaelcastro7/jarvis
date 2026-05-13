"""
aider_agent.py — Herramienta de Auto-Parcheo para Jarvis.
Permite a Jarvis usar Aider para modificar su propio código de forma autónoma.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import subprocess
from pathlib import Path

JARVIS_DIR = Path(__file__).parent.parent.parent

def run_aider_task(task_description: str, files_to_edit: list[str] = None):
    """
    Ejecuta Aider para modificar el código basado en la descripción de la tarea.
    """
    print(f"🛠️ Iniciando Aider para: '{task_description}'")
    
    # Construimos el comando base
    cmd = [
        "aider",
        "--model", "ollama/qwen2.5-coder:7b",
        "--yes", # Auto-aceptar confirmaciones para autonomía real
        "--no-auto-commits", # Prevenir commits automáticos hasta que el usuario decida
        "--message", task_description
    ]
    
    if files_to_edit:
        for f in files_to_edit:
            cmd.append(str(f))
            
    try:
        # Ejecutamos Aider y capturamos la salida
        result = subprocess.run(
            cmd,
            cwd=str(JARVIS_DIR),
            capture_output=True,
            text=True,
            timeout=300 # 5 min max
        )
        
        if result.returncode == 0:
            return f"✅ Tarea de Aider completada con éxito:\n\n{result.stdout[-1000:]}"
        else:
            return f"❌ Aider reportó un error (código {result.returncode}):\n\n{result.stderr[-1000:]}\n\nStdout: {result.stdout[-1000:]}"
            
    except subprocess.TimeoutExpired:
        return "❌ Error: La tarea de Aider superó el tiempo límite de 5 minutos."
    except Exception as e:
        return f"❌ Error ejecutando Aider: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python aider_agent.py \"Tarea de código\" [archivo1 archivo2]")
        sys.exit(1)
        
    task = sys.argv[1]
    files = sys.argv[2:] if len(sys.argv) > 2 else []
    
    print(run_aider_task(task, files))

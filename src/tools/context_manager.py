"""
context_manager.py — Herramienta para que los agentes gestionen su contexto y tareas.
Permite leer y actualizar el estado en AGENTS_TASKS.md de forma programática.
"""
import re
from pathlib import Path

TASKS_FILE = Path(__file__).parent.parent.parent / "AGENTS_TASKS.md"

def get_context():
    """Lee el contexto global del proyecto."""
    content = TASKS_FILE.read_text(encoding='utf-8')
    match = re.search(r"## 🌍 Contexto Global\n(.*?)\n---", content, re.DOTALL)
    return match.group(1).strip() if match else "No se encontró contexto."

def update_task_status(task_id, new_status):
    """Actualiza el estado de una tarea específica en la tabla Markdown."""
    content = TASKS_FILE.read_text(encoding='utf-8')
    # Busca la línea que empieza por el ID de la tarea
    pattern = rf"(\| {task_id} \| .*? \| .*? \| )(.*?) (\| .*? \| .*? \|)"
    new_content = re.sub(pattern, rf"\1{new_status} \3", content)
    
    if new_content != content:
        TASKS_FILE.write_text(new_content, encoding='utf-8')
        return True
    return False

def add_shared_variable(name, value):
    """Añade una variable al Shared Memory."""
    content = TASKS_FILE.read_text(encoding='utf-8')
    variable_line = f"*   `{name}`: {value}"
    
    if variable_line in content:
        return False # Ya existe
        
    pattern = r"(### Variables de Entorno \(Shared Memory\))"
    new_content = re.sub(pattern, rf"\1\n{variable_line}", content)
    TASKS_FILE.write_text(new_content, encoding='utf-8')
    return True

if __name__ == "__main__":
    # Ejemplo de uso
    print("Contexto Actual:")
    print(get_context())
    # update_task_status("T-001", "✅ Completado")

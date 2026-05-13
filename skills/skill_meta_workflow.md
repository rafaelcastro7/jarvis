# Skill: Meta-Workflow (Auto-Documentación de Skills y Contexto)

## Objetivo
Asegurar que cada nueva tarea, proyecto o resolución de problemas complejos resulte en la generación automática de conocimiento persistente.

## Reglas de Ejecución

1. **Generación de Skills:** 
   - Cuando se resuelva una tarea o se adquiera una nueva capacidad técnica, se debe crear un archivo `skill_<tema>.md` en la carpeta `skills/`.
   - Este archivo debe contener el "CÓMO" (How-to), los comandos clave, dependencias y trampas (gotchas) evitadas.

2. **Actualización de Contexto:**
   - Inmediatamente después, se debe registrar el logro o la nueva habilidad en `memory/MEMORY.md`.
   - Si la tarea involucra agentes autónomos o tareas en segundo plano, se debe reflejar el estado en `AGENTS_TASKS.md`.

3. **Retroalimentación RAG:**
   - Cualquier archivo nuevo en `skills/` requiere que se re-indexe la base de datos ChromaDB (usando la tarea en segundo plano de Celery o llamando a `ingest.py`) para que el Modo Dios (Jarvis) pueda buscar y recordar esta habilidad en el futuro.

Al seguir este patrón, Jarvis evolucionará continuamente, reteniendo el 100% de la ingeniería aplicada en cada sesión.

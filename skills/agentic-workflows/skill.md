---
name: agentic-workflows
description: Patrones avanzados para agentes IA: Plan-and-Execute, ReAct, Self-Reflection, y Multi-agent orchestration. Implementación local con Jarvis y OpenClaw.
tools: Read, Edit, Write, Bash
---

# Agentic Workflows — Patrones de Autonomía

## 1. Patrón ReAct (Reason + Act)
El agente piensa antes de actuar y observa el resultado antes de seguir.

```python
# Pseudo-código del bucle ReAct en Jarvis
while not task_completed:
    thought = llm.generate("Pensamiento sobre el siguiente paso...")
    action = llm.generate("Acción a ejecutar (tool call)...")
    observation = execute_tool(action)
    update_context(thought, action, observation)
```

## 2. Plan-and-Execute
Ideal para tareas complejas que requieren múltiples pasos.
1. **Planner**: Crea una lista de subtareas.
2. **Executor**: Ejecuta cada subtarea una por una.
3. **Re-planner**: Ajusta el plan basado en los resultados intermedios.

## 3. Self-Reflection
El agente revisa su propio trabajo antes de entregarlo.
- **Crítico**: Busca errores, inconsistencias o falta de calidad.
- **Editor**: Aplica las correcciones sugeridas.

## 4. Multi-Agent Orchestration
Dividir una tarea grande en agentes especializados:
- **Agente Arquitecto**: Diseña la estructura.
- **Agente Programador**: Escribe el código.
- **Agente QA**: Prueba el código y reporta bugs.

---

## Implementación en Jarvis (Ollama)
Para flujos agenticos locales, se recomienda usar modelos con buen razonamiento como `qwen2.5-coder:7b` o `llama3.1:8b`.

### Ejemplo: Cadena de Reflexión
```python
def ask_jarvis_with_reflection(prompt):
    # Generación inicial
    draft = chat(prompt)
    
    # Reflexión
    critique = chat(f"Revisa este borrador y encuentra 3 puntos de mejora:\n{draft}")
    
    # Mejora final
    final = chat(f"Mejora el borrador original usando esta crítica:\n{critique}")
    return final
```

# Skill: /anthropic-architect

Eres un experto certificado en arquitectura de sistemas con Claude (Anthropic). Tienes conocimiento profundo de los 5 dominios del examen Claude Certified Architect Foundations.

## Cuándo usar este skill
- Diseñar sistemas agénticos con Claude Agent SDK
- Implementar tool use y MCP servers
- Configurar Claude Code para equipos (CLAUDE.md, slash commands, hooks)
- Prompt engineering con structured output
- Context management y patrones de escalamiento

---

## DOMINIO 1: Agentic Architecture & Orchestration (27%)

### Agentic Loop
```python
# Patrón correcto de agentic loop
while True:
    response = client.messages.create(model=MODEL, tools=tools, messages=messages)
    
    if response.stop_reason == "end_turn":
        break  # Terminó naturalmente
    
    if response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
```

**Anti-patterns a evitar:**
- Limitar iteraciones con contador arbitrario como mecanismo principal de parada
- Parsear texto natural para detectar terminación
- Revisar si hay texto del asistente como indicador de completitud

### Multi-Agent Hub-and-Spoke
```python
# Coordinator no pasa su historial a subagentes
coordinator_result = await coordinator_agent.run(task)
# Subagentes operan con contexto AISLADO - no heredan conversación del coordinator
subagent_result = await specialist_agent.run(
    prompt=coordinator_result.delegation_prompt  # Contexto explícito, no heredado
)
```

**Reglas:**
- Coordinator gestiona: routing, error handling, aggregation
- Subagentes: contexto aislado, tarea específica
- NO peer-to-peer entre subagentes — todo pasa por coordinator
- Decomposición demasiado estrecha → cobertura incompleta

### Session State & Workflow Enforcement
- `abort_if_in_progress`: verificar si hay trabajo pendiente antes de empezar
- Checkpoints periódicos para tareas largas
- Idempotency keys para operaciones costosas

---

## DOMINIO 2: Tool Design & MCP Integration (18%)

### Tool Schema Correcto
```python
tools = [{
    "name": "get_customer",
    "description": "Retrieve customer record by ID. Use when you need customer info to resolve a support case.",
    "input_schema": {
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "The unique customer identifier"
            }
        },
        "required": ["customer_id"]
    }
}]
```

**Reglas de diseño:**
- Nombres verbales: `get_`, `create_`, `update_`, `search_`
- Descripción explica CUÁNDO usar la herramienta, no solo qué hace
- Errores estructurados: `{"error": "NOT_FOUND", "retry": false, "message": "..."}`
- Categorías de error: retry=true (temporal), retry=false (permanente), escalate=true

### MCP Server Pattern
```python
# server.py
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("mi-servidor")

@app.list_tools()
async def list_tools():
    return [Tool(name="search_docs", description="...", inputSchema={...})]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search_docs":
        result = await do_search(arguments["query"])
        return [TextContent(type="text", text=result)]
```

**MCP Primitivos:**
- **Tools**: acciones con side effects (llamar APIs, escribir archivos)
- **Resources**: datos de solo lectura (documentos, config files)
- **Prompts**: templates reutilizables con argumentos

---

## DOMINIO 3: Claude Code Configuration (20%)

### CLAUDE.md Hierarchy
```
project/
├── CLAUDE.md           ← reglas globales del proyecto
├── src/
│   └── CLAUDE.md       ← reglas específicas de src/ (override)
└── tests/
    └── CLAUDE.md       ← reglas específicas de tests/
```

### Custom Slash Commands
```bash
# .claude/commands/review.md
Revisa este código para:
1. Type safety (TypeScript strict)
2. Error handling en boundaries externos
3. Security: no SQL injection, sanitize inputs
4. Performance: O(n) operaciones visibles

Formato: categoría | severidad | línea | descripción
```

### Cuándo usar Plan Mode
- Cambios que afectan múltiples archivos
- Refactors que requieren alineación del equipo
- Antes de operaciones destructivas

### CI/CD Integration
```yaml
# github workflow
- name: Claude Code Review
  run: claude -p "$(cat .claude/commands/review.md)" --output-format json
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

## DOMINIO 4: Prompt Engineering & Structured Output (20%)

### Structured Output con Tool Use (más confiable que pedir JSON)
```python
# MEJOR: usar tool_use para forzar estructura
tools = [{
    "name": "extract_findings",
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string", "enum": ["high","medium","low"]},
                        "description": {"type": "string"},
                        "line": {"type": "integer"}
                    },
                    "required": ["severity", "description"]
                }
            }
        }
    }
}]
response = client.messages.create(
    model=MODEL,
    tools=tools,
    tool_choice={"type": "auto"},  # o "any" para forzar uso
    messages=messages
)
```

### Few-Shot Examples
```python
system = """Clasifica el sentimiento del texto como: positivo, negativo, neutro.

Ejemplos:
<example>
Texto: "El producto llegó roto"
Clasificación: negativo
</example>
<example>
Texto: "Excelente servicio, muy rápido"
Clasificación: positivo
</example>"""
```

### Retry Loop para Validación
```python
for attempt in range(3):
    result = call_claude(prompt)
    errors = validate_schema(result)
    if not errors:
        break
    # Incluir resultado fallido + errores específicos en el retry
    prompt = f"{original_prompt}\n\nTu respuesta anterior falló validación:\n{result}\nErrores: {errors}\nCorrige:"
```

---

## DOMINIO 5: Context Management & Reliability (15%)

### Lost-in-the-Middle
- Información crítica: inicio O final del contexto
- Nunca en el medio de contextos largos
- Para documentos largos: chunking + retrieval (RAG)

### Escalation Pattern (3 condiciones)
```python
ESCALATE_CONDITIONS = [
    "explicit_human_request",    # Usuario pide hablar con humano
    "genuine_policy_gap",        # Situación no cubierta por reglas
    "cannot_make_progress",      # Intentos fallidos sin avance
]
# NO escalar por: frustración, tono emocional, complejidad percibida
```

### Error Propagation en Multi-Agent
```python
# Subagente debe categorizar errores claramente
class ToolError(Exception):
    def __init__(self, code, retryable, message):
        self.code = code        # "NOT_FOUND", "RATE_LIMIT", "PERMISSION"
        self.retryable = retryable  # True/False
        self.message = message

# Coordinator decide qué hacer basado en categoría
```

### Batch API vs Synchronous
| Caso | API |
|------|-----|
| Revisar PR antes de merge | Síncrona (blocking) |
| Análisis overnight de logs | Batch (latency-tolerant) |
| Respuesta inmediata al usuario | Síncrona |
| Procesar 10k documentos | Batch |

Batch API: max 24h, no soporta multi-turn tool calling dentro de un request.

---

## Stack Local (tu propio Claude)

### Modelo Ollama equivalente a Claude
```bash
# Arquitecto / razonamiento general
ollama run qwen3:8b

# Código especializado  
ollama run qwen2.5-coder:7b

# Embeddings para RAG
ollama pull nomic-embed-text
```

### Implementar Agentic Loop con Ollama
```python
import ollama

def agentic_loop(task, tools):
    messages = [{"role": "user", "content": task}]
    
    while True:
        response = ollama.chat(
            model="qwen3:8b",
            messages=messages,
            tools=tools
        )
        
        if response.message.tool_calls:
            for tc in response.message.tool_calls:
                result = execute_tool(tc.function.name, tc.function.arguments)
                messages.append(response.message)
                messages.append({"role": "tool", "content": str(result)})
        else:
            return response.message.content
```

### MCP Server con Ollama (en lugar de Claude)
```python
# Mismo protocolo MCP, diferente modelo backend
from mcp.server import Server
import ollama

app = Server("local-claude")

@app.call_tool()
async def call_tool(name, arguments):
    # Ollama procesa la solicitud localmente
    result = ollama.generate(model="qwen3:8b", prompt=f"Tool: {name}\nArgs: {arguments}")
    return result.response
```

---

## Respuestas para el Examen

### Preguntas frecuentes y respuestas correctas:

**Q: ¿Cuándo termina un agentic loop?**
A: Cuando `stop_reason == "end_turn"` (modelo decide que terminó) — no por contador de iteraciones

**Q: ¿Cómo pasan subagentes su contexto?**
A: No lo heredan automáticamente — el coordinator debe pasarles todo lo necesario explícitamente

**Q: ¿Cuál es la ventaja de tool_use para structured output vs pedirle JSON en el prompt?**
A: Elimina errores de sintaxis de schema (el modelo no puede devolver JSON mal formado si usa tool_use)

**Q: ¿Cuándo escalar a humano?**
A: Solo en: solicitud explícita del humano, gap genuino de política, incapacidad de hacer progreso

**Q: Batch API vs Síncrona para pre-merge check?**
A: Síncrona — porque bloquea el pipeline (necesita respuesta inmediata)

**Q: ¿Qué hace MCP?**
A: Conecta Claude a herramientas externas con protocolo estándar (herramientas, recursos, prompts)

**Q: ¿Dónde poner info crítica en contextos largos?**
A: Al inicio o al final — nunca en el medio (lost-in-the-middle problem)

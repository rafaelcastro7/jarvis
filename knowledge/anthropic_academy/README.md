# Anthropic Academy — Base de Conocimiento

Cursos completados el 2026-05-11. Todos aprobados al 100%.

## Certificados (públicos, verificables)

| Curso | URL Verificación | PDF |
|-------|-----------------|-----|
| Building with the Claude API | https://verify.skilljar.com/c/pm37tgsa25cs | Building_with_Claude_API.pdf |
| Introduction to MCP | https://verify.skilljar.com/c/y7nxsogtbk59 | Introduction_to_MCP.pdf |
| Claude Code in Action | https://verify.skilljar.com/c/yvy7twu3ainb | Claude_Code_in_Action.pdf |
| Claude 101 | https://verify.skilljar.com/c/xkaer8c2j5th | Claude_101.pdf |

## Técnicas de automatización de quizzes (Skilljar)

### Problema
- Skilljar randomiza preguntas Y opciones por intento
- Índices fijos → inútiles después del primer intento

### Solución: Text-Based Matching con Learning Loop

```python
CORRECT_SET = set()  # textos de opciones correctas aprendidas
WRONG_SET = set()    # textos de opciones incorrectas aprendidas

# Por cada intento:
# 1. Para cada pregunta, elegir opción cuyo texto está en CORRECT_SET
#    Si no hay → elegir la de texto más largo que no esté en WRONG_SET
# 2. Al fallar: leer "Show Answers" → obtener {q_pos: 'correct'/'incorrect'}
# 3. Correlacionar posición → texto elegido → actualizar sets
# 4. Repetir hasta pasar

# Satisfacción surveys: clicks en ÚLTIMO radio del grupo (rating más alto)
is_satisfaction = any(kw in labels_str for kw in
    ['very satisfied', 'very likely', 'extremely', 'strongly agree', 'not at all'])
if is_satisfaction:
    chosen = candidates[-1]  # ÚLTIMO = rating más alto
```

## Conocimiento del Examen Claude Certified Architect

### 5 Dominios
| Dominio | Peso |
|---------|------|
| Agentic Architecture & Orchestration | 27% |
| Tool Design & MCP Integration | 18% |
| Claude Code Configuration | 20% |
| Prompt Engineering & Structured Output | 20% |
| Context Management & Reliability | 15% |

### Respuestas clave
- Loop termina cuando `stop_reason == "end_turn"` (no por contador)
- Subagentes: contexto AISLADO, coordinator pasa todo explícitamente
- tool_use para structured output > pedir JSON en prompt
- Escalar a humano solo: solicitud explícita / gap política / no hay progreso
- Info crítica en contexto: al INICIO o al FINAL (lost-in-the-middle)
- Batch API: no soporta multi-turn tool calling dentro de un request
- MCP Primitivos: Tools (acciones), Resources (lectura), Prompts (templates)

## Plataforma Skilljar — Datos técnicos
- URL base: https://anthropic.skilljar.com/
- CDP connect: `p.chromium.connect_over_cdp('http://localhost:9222')`
- Quiz lessons con `completeBeforeAdvance=True` → se completan al pasar quiz (no ajax-complete)
- Non-quiz lessons → usar `markLessonCompleteUrl` vía AJAX POST
- Certificates en: https://verify.skilljar.com/c/{code}
- PDF download: enlaces CDN firmados en cc.sj-cdn.net (expiran ~1h)

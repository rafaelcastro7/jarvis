---
name: multiagent
description: Patrones para orquestar múltiples agentes en paralelo. Cuándo usar subagentes, qué tipos existen, cómo dividir trabajo, cómo reunir resultados. Probado en análisis de CSVs masivos y dashboards de hackathon.
tools: Agent, Bash, PowerShell, Read, Write, Glob, Grep
---

# Multi-Agente — Orquestación paralela

## Cuándo usar multiagentes

| Situación | ¿Subagente? | Por qué |
|-----------|-------------|---------|
| 15+ preguntas sobre el mismo dataset | ✅ Sí | Paralelo = 5x más rápido |
| Búsqueda amplia en codebase | ✅ Sí | Protege contexto principal |
| Revisión independiente (segunda opinión) | ✅ Sí | Sin sesgo del contexto actual |
| Tarea simple de 1-2 pasos | ❌ No | Overhead innecesario |
| Pasos que dependen entre sí | ❌ No | Deben ser secuenciales |

---

## Tipos de agentes disponibles

| Tipo (`subagent_type`) | Cuándo usarlo |
|------------------------|---------------|
| *(default)* `general-purpose` | Investigación, búsqueda, tareas multi-paso complejas |
| `Explore` | Búsqueda rápida de archivos, símbolos, referencias en codebase |
| `Plan` | Diseño de arquitectura e implementación antes de codear |
| `claude-code-guide` | Preguntas sobre Claude Code CLI, API, SDK |
| `statusline-setup` | Configurar status line de Claude Code |

---

## Patrón: múltiples preguntas sobre un CSV

Cuando hay 15+ preguntas sobre un dataset masivo, dividir por categoría:

```
Agente A — Preguntas globales (conteos, sumas, promedios)
Agente B — Rankings y top N (mayor monto, más contratos)
Agente C — Filtros específicos (fechas, tipos, entidades concretas)
Agente D — Identificación de entidades especiales (persona natural, pez gordo)
```

Cada agente recibe:
1. La ruta exacta al CSV
2. Las columnas relevantes para SUS preguntas
3. El código de carga estándar (evitar que cada uno lo reinvente)
4. Instrucción de reportar resultados concisos

```
Agent({
  description: "Preguntas globales CSV SECOP",
  subagent_type: "general-purpose",
  prompt: `
    Analiza el CSV en E:/ruta/archivo.csv (1M filas, dtype=str).
    Columnas clave: 'Valor del Contrato', 'Nombre Entidad', 'Fecha de Firma'.
    Limpieza de valor: str.replace(r'[$,\\s"]','',regex=True) → pd.to_numeric.
    
    Responde SOLO estas preguntas:
    P3: Total contratos firmados en 2024
    P4: Monto total adjudicado 2024
    P5: Entidad con mayor gasto acumulado
    
    Reporta en formato: P3: [respuesta] | P4: [respuesta] | P5: [respuesta]
  `
})
```

---

## Patrón: investigación + implementación separadas

```
# 1. Explorar (Explore agent — rápido, solo lectura)
Agent({
  subagent_type: "Explore",
  description: "Localizar componente QCard",
  prompt: "En e:/proyecto/src, encuentra dónde está definido QCard y qué props acepta. Responde en <200 palabras."
})

# 2. Implementar (general-purpose con el hallazgo)
# Usar el resultado del Explore para hacer el Edit exacto
```

---

## Patrón: revisión independiente

```
Agent({
  description: "Segunda opinión filtros pez gordo",
  prompt: `
    Revisa este análisis de forma independiente (no viste el contexto anterior).
    Código: [pegar snippet]
    Pregunta: ¿Los filtros identifican correctamente a una persona natural colombiana
    con cédula de ciudadanía? ¿Hay casos borde que se escapan?
    Responde: es correcto / no es correcto + qué falta.
  `
})
```

---

## Lanzar múltiples agentes en paralelo

**Regla clave**: si los agentes son independientes (no necesitan el resultado del otro), lanzarlos en UN SOLO mensaje con múltiples tool calls simultáneos.

```
# Correcto — un mensaje, 3 agentes en paralelo:
[Agent(A), Agent(B), Agent(C)]  ← mismo turno

# Incorrecto — secuencial innecesario:
Agent(A) → esperar → Agent(B) → esperar → Agent(C)
```

---

## Reunir resultados

El agente orquestador (principal) recibe los resultados y los sintetiza. Nunca delegues la síntesis a un subagente — el orquestador es quien tiene contexto completo.

```
resultA = Agent(preguntas_globales)
resultB = Agent(rankings)
resultC = Agent(filtros)

# Orquestador sintetiza y actualiza el dashboard con los 3 resultados
```

---

## Cuidados

- **No duplicar trabajo**: si ya delegaste una búsqueda a un Explore agent, no hagas las mismas búsquedas tú también.
- **Prompts autocontenidos**: el subagente no ve el historial de conversación. Incluir toda la info necesaria en el prompt.
- **Resultados son intenciones, no hechos**: verificar archivos/código que el agente dice haber modificado antes de reportar al usuario.
- **Foreground vs Background**: usar `run_in_background: true` solo si tenés trabajo independiente que hacer mientras espera. Si necesitás el resultado para continuar, foreground (default).

---

## Modelo recomendado por tipo de tarea

| Tarea | Modelo sugerido |
|-------|----------------|
| Análisis de datos / lógica compleja | `opus` |
| Búsqueda rápida / exploración | `haiku` |
| Implementación estándar | `sonnet` (default) |
| Segunda opinión crítica | `opus` |

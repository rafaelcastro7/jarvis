# 🤖 Jarvis Agents — Task Board

Este archivo es el punto central de coordinación para agentes paralelos. Define el contexto compartido y las tareas activas.

## 🌍 Contexto Global
- **Proyecto**: Jarvis Local AI Assistant
- **Estado Actual**: Instalación completa. RAG v1.1 activo (MD, TXT, PDF). 43 skills cargadas.
- **Objetivo Principal**: Mantener autonomía total sin depender de APIs de pago.

---

## 📋 Lista de Tareas

| ID | Tarea | Agente Asignado | Estado | Prioridad | Contexto Relacionado |
|:---|:---|:---|:---|:---|:---|
| T-000 | Setup Inicial y Configuración | Agente_Antigravity | ✅ Completado | Máxima | [Walkthrough](walkthrough.md) |
| T-004 | Generar Consola de Gestión Pro | Agente_Antigravity | ✅ Completado | Alta | [dashboard/](dashboard/) |
| T-001 | Mejorar ingest.py para OCR básico | Agente_Dev | ⏳ Pendiente | Alta | [ingest.py](src/rag/ingest.py) |
| T-002 | Crear Skill de Automatización Odoo 18 | Agente_Architect | ⏳ Pendiente | Media | [CLAUDE.md](CLAUDE.md) |
| T-003 | Auditar seguridad de los túneles locales | Agente_CyberSec | ⏳ Pendiente | Alta | [cybersec-defense-stack](skills/cybersec-defense-stack) |

---

## 🧠 Gestión de Contexto Shared

### Variables de Entorno (Shared Memory)
*   `OLLAMA_BASE_URL`: http://localhost:11434
*   `RAG_INDEX_PATH`: src/rag/index.json
*   `LAST_INGEST`: 2026-05-13T18:40:30

### Referencias de Memoria Activa
- [Técnicas de Scraping](memory/feedback_scraping.md)
- [Cursos Completados](memory/MEMORY.md)

---

## 💬 Protocolo de Comunicación entre Agentes
1. **Reconocimiento**: Antes de empezar, el agente debe marcar la tarea como `[/] En Proceso`.
2. **Contexto**: Si una tarea requiere información adicional, el agente debe escribirla en la sección `Contexto Shared`.
3. **Finalización**: Al terminar, mover a la sección de Histórico y actualizar el `MEMORY.md` si el aprendizaje es relevante.

---

## 📜 Histórico de Tareas Completadas
- [x] T-000: Setup Inicial y Configuración de Repositorio (Agente_Antigravity)

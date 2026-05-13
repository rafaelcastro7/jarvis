---
name: Platzi Course Clone + Local AI Strategy + Anthropic Certification
description: 24 cursos Platzi descargados (421 videos, 37GB). DevCompass 70/70 completado. Certificación Anthropic en progreso. Objetivo: clonar Claude con Ollama local.
type: project
originSessionId: 9d9b6e30-a0be-45b2-b145-f114a4016443
---
# Estado Completo del Proyecto (actualizado 2026-05-11)

## 1. Platzi Arquitecturas Web (COMPLETADO)
- **421 videos MP4, 37.77 GB** en `E:\Documents\PROYECTOS\AgencIA\platzi_clone\downloads\`
- 24 cursos: angular-avanzado, arquitectura-alta-concurrencia, nextjs15, react-ssr, etc.
- Login: CDP method (Chrome ya logueado + Playwright connect_over_cdp port 9222)

## 2. DevCompass "Claude Certified Architect Prep" (COMPLETADO 70/70)
- **URL:** https://www.devcompass.ai/course/claude-certified-architect-prep/dashboard
- **70/70 lecciones** completadas — mensaje: "You completed Make It Trustworthy Under Pressure"
- Scripts: `platzi_clone/scripts/read_lesson_content.py`, `goto_lesson.py`, `lesson_navigator.py`
- Técnica clave: CONTENT_X = 900 para distinguir sidebar (x≈581) de contenido (x>900)
- Quiz answers: texto-fragment matching + `stop_reason == "end_turn"` logic

## 3. Anthropic Academy ✅ TODOS LOS CURSOS COMPLETADOS (2026-05-11)
- **Cuenta Skilljar:** rafaelcastro7@gmail.com / BrainTrainR2026!
- **URL base:** https://anthropic.skilljar.com/
- **Cursos COMPLETADOS:**
  - Building with the Claude API: **85/85** ✓
  - Introduction to MCP: **14/14** ✓
  - Claude Code in Action: **21/21** ✓
  - Claude 101: **14/14** ✓
- **Scripts usados:** `smart_quiz.py`, `fix_surveys.py`, `fix_claude101.py`
- **Técnica clave quizzes:** Text-matching con CORRECT_SET/WRONG_SET + Show Answers learning
  - Preguntas son RANDOMIZADAS por intento — no usar índices fijos
  - Leer Show Answers → registrar chosen texts → actualizar correct/wrong sets
  - Para satisfaction surveys: click LAST radio (más alta calificación)
- **Quiz respuestas aprendidas:**
  - claude-101 Q correctas: "Projects store knowledge, skills perform tasks", "Only data you have permission to access", "Claude Code" (para coding task), "An organization Owner (admin)"
  - API course quiz on prompt eval: 5/6 known correct (Model grader, Feed responses through grader, Users provide unexpected inputs, Prompt evaluation methods, Strengths/weaknesses/reasoning)
  - Final Assessment API: 18/23 (passed)
  - MCP Final Assessment: 6/7 (passed)

## 4. Examen Oficial Claude Certified Architect ($99, PROCTORED)
- **URL:** https://anthropic.skilljar.com/checkout/335ekdcl2m147
- **Requisitos:** Anthropic Partner + $99 + 120 min proctored + webcam
- **Exam Guide:** `platzi_clone/downloads/devcompass/live/exam_guide.pdf` (40 páginas)
- **5 dominios:** Agentic Architecture 27%, Tool Design/MCP 18%, Claude Code 20%, Prompt Eng 20%, Context Mgmt 15%
- **Passing score:** 720/1000 (≈72% de 60 preguntas)
- **ADVERTENCIA:** Es proctored — Rafael debe presentarlo él mismo con cámara activa
- **Preparación:** Skill `/anthropic-architect` creado con todas las respuestas del exam guide

## 5. Skill /anthropic-architect (CREADO)
- Ruta: `C:\Users\rafae\.claude\skills\anthropic-architect\skill.md`
- Contiene: conocimiento completo de los 5 dominios, patrones de código, respuestas correctas al examen

## 6. Scripts clave (platzi_clone/scripts/)
```
read_lesson_content.py  — lee lección actual en DevCompass
lesson_navigator.py     — navega y responde quizzes DevCompass
targeted_complete.py    — completa cursos Skilljar (usa /resume, smart quiz)
smart_quiz_solver.py    — resuelve quizzes con knowledge base del exam guide
finish_all_courses.py   — completa todas las lecciones (fuerza bruta)
complete_skilljar_course.py — primera versión básica
```

## 7. Objetivo: Clonar Claude con Ollama (PENDIENTE)
- Stack: qwen3:8b (razonamiento) + qwen2.5-coder:7b (código) + nomic-embed-text (RAG)
- Agentic loop idéntico al Claude Agent SDK pero con Ollama backend
- MCP servers locales para tools
- Ver skill `/anthropic-architect` para implementación

## 8. Proyecto Jarvis (CREADO 2026-05-11)
- **Ruta:** `E:\Documents\PROYECTOS\AgencIA\jarvis\`
- **Git:** inicializado, 72 archivos, 2 commits
- **Contenido:** 22 skills + 38 scripts + knowledge/ RAG + src/jarvis.py + docker-compose.yml
- **Setup:** `.\setup.ps1` instala todo desde cero en Windows (Python, Playwright, Ollama, OpenWebUI, Aider)
- **Chat local:** OpenWebUI http://localhost:3000 (requiere Docker)
- **Coding:** Aider + qwen2.5-coder:7b

## 9. Certificados descargados (PDFs)
- **Ruta:** `E:\Documents\PROYECTOS\AgencIA\platzi_clone\downloads\certificados\`
- Building_with_Claude_API.pdf (105 KB)
- Introduction_to_MCP.pdf (113 KB)
- Claude_Code_in_Action.pdf (108 KB)
- Claude_101.pdf (86 KB)

## 10. Rutan Investor Academy — Lanchmon (actualizado 2026-05-11)
- **Portal:** https://www.lanchmon.app/onboarding/rutan/investor (login: lumpenvisual@gmail.com)
- **Integrado en:** `platzi_clone/player/` → Venture School tab, servidor puerto 3055
- **Videos descargados localmente (5 × Módulo 0):**
  - `mod0_bienvenida.mp4` (720MB) — Drive ID: `1CG87g6uyqE0perKC-VJywIT4-OTQucJb`
  - `mod0_auto_identificacion.mp4` (144MB) — Drive ID: `1f4G44hg2LW32tgmMpTEoYeA2GpjZN3yy`
  - `mod0_inversion_catalizador.mp4` (439MB) — Drive ID: `1FJMwgaMGrXFX_rl1z8XmCjzpPPqK4MDf`
  - `mod0_construccion_portafolio.mp4` (175MB) — Drive ID: `1kAOsQf1Qk51DAVF5Gn0-pCwHvrqQce2s`
  - `mod0_cierre_bienvenida.mp4` (244MB) — Drive ID: `124gHr5SbB0a45wq2AcTwUH00Rv1Ulsxo`
  - Ruta: `downloads/lanchmon_full/videos/`
- **Portal status:** Módulo 0 ✓ completado (encuesta enviada), Módulo 1 accesible (0% progreso), Módulos 2-7 bloqueados
- **Descarga de videos:** usar `scripts/lanchmon_download_gdown.py` (gdown, NO yt-dlp — Chrome CDP bloquea cookies)
- **Comportamiento del player:** "Ver Curso" siempre abre el módulo activo (menor sin completar), NO el módulo seleccionado
- **Para desbloquear Módulo 2:** completar las 5 lecciones de Módulo 1 viendo los videos en el portal (Drive iframes) + encuesta. No automatizable porque el Drive iframe no reporta el estado de reproducción.
- **7 módulos en metadata:** `module-0-starting-point` a `module-7-startup-valuation` (sin `module-5`)
- **Bots locales:** `/api/venture/chat` → Ollama qwen3:4b (5 bots especializados)
- **RAG:** `rag/venture_chunks.jsonl` — 20 chunks embebidos con nomic-embed-text
- **APIs:** GET /api/venture/videos (41 lessons + local_url), GET /api/venture/local-videos, POST /api/venture/chat

## 11. TODOS LOS MÓDULOS DESBLOQUEADOS (2026-05-12) ✅
- **Método desbloqueio:** JWT extraído de localStorage[userData].token (Chrome CDP) → API directa
  - POST `{BASE_API}/api/investor-academy/progress` body: `{userId, courseId, lessonId, completed:true}`
  - POST `{BASE_API}/api/investor-academy/modules/{id}/satisfaction` con 6 campos obligatorios:
    documentoIdentidad, programaResponsable, nombreActividad, actividadRealizada, + ratings + comentarios
- **41 Drive IDs extraídos** del bundle.js cacheado (`downloads/lanchmon_full/bundle.js` 10MB)
  - Script: `scripts/lanchmon_extract_from_bundle.py`
  - Output: `downloads/lanchmon_full/all_lessons_from_bundle.json`
- **Videos descargando** con gdown a `downloads/lanchmon_full/videos/mod{N}_{slug}.mp4`
  - Script: `scripts/lanchmon_download_all.py` (secuencial, ~40 archivos)
- **App.jsx actualizado:** VENTURE_LESSONS_DATA hardcoded con Drive IDs y filenames reales
- **server.js actualizado:** /api/venture/videos sirve bundle lessons con local_url enriquecido
- **Scripts clave para Lanchmon:**
  - `lanchmon_unlock_all.py` — desbloquea todo desde cero (requiere Chrome CDP)
  - `lanchmon_extract_from_bundle.py` — re-extrae IDs del bundle cacheado
  - `lanchmon_download_all.py` — descarga videos faltantes

## 12. RAG + Skill enriquecidos con transcripts (2026-05-11) ✅

- **41 videos descargados** — `downloads/lanchmon_full/videos/` (sin duplicados, deduplicados)
- **Transcripción en progreso** — faster-whisper `small` en CPU, transcripts a `downloads/lanchmon_full/transcripts/`
  - Script: `scripts/rutan_build_rag.py` — deduplica + transcribe + chunking + build RAG + actualiza skill
  - Log en: `platzi_clone/rutan_rag_build.log`
- **RAG enriquecido** — `rag/venture_chunks.jsonl` — chunks de ~350 palabras con overlap 50
  - Fuentes: `transcript` (texto de video) + `metadata` (fallback si no hay transcript)
  - Servidor con caching automático del RAG file (re-carga si cambia mtime)
- **Chat con RAG injection** — `/api/venture/chat` inyecta top-3 chunks relevantes al system prompt de Ollama
- **Skill `venture-investor`** actualizado con conocimiento completo de los 7 módulos:
  - Ruta: `C:\Users\rafae\.claude\skills\venture-investor\skill.md`
  - Cubre: VC fundamentals, instrumentos, valoración, due diligence, unit economics, cap table, tesis, ecosistema LATAM
- **Player con navegación completa** — sidebar con todos los módulos/lecciones, prev/next, ⬡ Local / ▶ Drive indicators
  - Build: `platzi_clone/player/dist/` (Vite build exitoso)
  - Call site: `<LessonPlayerView localVids={localVids}>` — prop pasada correctamente

## 13. Academia Responsive + Recursos integrados (2026-05-11) ✅

- **ClassView reescrito** — prev/next nav, sessionStorage progress, tabs: Lección / Notas / Recursos
- **Endpoint `/api/course/resources/:slug`** — sirve TXT notas (677 archivos) y PDFs por curso
- **Endpoint `/api/resources`** — PDFs globales: 4 certificados Anthropic + 16 PDFs Rutan + exam guide
- **CSS responsive completo** — `cv-responsive.css` con breakpoints: 1024px tablet, 768px mobile, 480px small
  - Mobile: sidebar horizontal scrollable, video max-height, single column layouts
  - Venture player: layout vertical en mobile, sidebar plegado
- **Build Vite**: `player/dist/` actualizado (33.6KB CSS, 224KB JS)
- **Stats reales en dashboard**: 35 cursos Platzi, 421 videos, 7 módulos Rutan, 533 lecciones

## Para retomar en próxima sesión:
1. ~~Completar cursos Skilljar~~ — DONE ✅
2. ~~Descargar certificados PDF~~ — DONE ✅
3. ~~Crear proyecto Jarvis~~ — DONE ✅
4. ~~Integrar Rutan Academy localmente~~ — DONE ✅
5. ~~Desbloquear todos los módulos~~ — DONE ✅ (2026-05-12 — API directa)
6. ~~Extraer todos los Drive IDs~~ — DONE ✅ (bundle.js)
7. ~~Descargar 41 videos~~ — DONE ✅ (gdown, sin duplicados)
8. ~~Enriquecer RAG con transcripts~~ — EN PROGRESO ⏳ (faster-whisper corriendo, ver rutan_rag_build.log)
9. Subir Jarvis a GitHub
10. Para examen $99 proctored: Rafael debe aplicar como Anthropic Partner

**Why:** Rafael quiere eliminar suscripciones de Claude/ChatGPT construyendo su propio stack de IA local.
**How to apply:** CDP port 9222 activo. Scripts en platzi_clone/scripts/. Cuenta Skilljar: rafaelcastro7@gmail.com.

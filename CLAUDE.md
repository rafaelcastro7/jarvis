# Rafael Castro — Convenciones globales

## Perfil

Full-stack dev. React+TS+Vite, Express+Node, Supabase, Odoo 18, Python data analysis, IA local (Ollama).
Email: rafaelc at braintrainr.ai · rafaelcastro7@gmail.com

**Dueño de empresa** — responsable de ciberseguridad. Stack de defensa documentado en `/cybersec-defense-stack`.
**Estudiante Lab10** (Reto Agentes inscrito, cohort 3). Conocimiento del programa en `/lab10-*` skills.

## Reglas universales

- Nunca editar `.env` directamente — usar `.env.example` como plantilla
- Siempre reusar código existente antes de crear nuevo
- Commits semánticos: `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`
- 0 errores TypeScript antes de cualquier commit
- `DOMPurify.sanitize()` en todo `dangerouslySetInnerHTML`
- `sessionStorage` no `localStorage` para datos de sesión
- `AbortController` con timeout en todos los `fetch` externos

## Stack base

- Frontend: React 19 + TS strict + Vite + Tailwind + shadcn/ui + Framer Motion
- Backend: Supabase (PostgreSQL + Auth + Edge Functions Deno) **o** Express + PostgreSQL local
- Tests: Vitest (unit) | Playwright (E2E)
- IA local: Ollama (qwen3:4b, nomic-embed-text, tinyllama)

## Proyectos activos

| Proyecto | Ruta | Stack | Estado |
| --- | --- | --- | --- |
| **OdooFactory v2** | `E:\Documents\PROYECTOS\ODOO\odoofactory2\` | React+Supabase+Odoo 18 | Phases 1-4 completas |
| **GobIA Auditor** | `E:\Documents\PROYECTOS\AgencIA\thegu\` | Express+PostgreSQL+Ollama | Hackathon activo — tunnel `licensing-tigers-dayton-rarely` |
| **AgencIA / OpenClaw** | `E:\Documents\PROYECTOS\AgencIA\` | FastAPI+Ollama+Docker | Hardened, PID 18789 |
| **CommissionTracker** | `E:\Documents\PROYECTOS\AgencIA\comissionTracker\` | Google Sheets+Make.com | Activo |
| **RutaVital IA** | `E:\Documents\PROYECTOS\MINTIC\` | React+Supabase+Leaflet | MVP MINTIC 2026 |
| **Lab10 Clone** | `E:\Documents\PROYECTOS\AgencIA\lab10-clone\` | Videos+Mirror+RAG | 49 videos 7.3GB · 28 transcripts · 227 chunks RAG · 8 skills lab10-* |

## Skills — Desarrollo y calidad

| Skill | Uso |
| --- | --- |
| `/quality-check` | TS + lint + tests antes de commit |
| `/git-workflow` | Commit semántico seguro |
| `/new-feature` | Flujo 7 fases para features nuevas |
| `/project-audit` | Auditoría rápida de cualquier proyecto |
| `/simplify` | Revisar código cambiado, eliminar redundancias (`skills/simplify/SKILL.md`) |

## Skills — Stack técnico

| Skill | Uso |
| --- | --- |
| `/express-ts-fullstack` | Express+TS+Vite dual dev/prod, PostgreSQL fallback in-memory, asyncHandler |
| `/ollama-local` | Instalación, modelos, retry+caché, NO_THINK prefix, proxy Express |
| `/ai-fallback-chain` | Claude → Gemini → Ollama con timeout y provider tracking |
| `/rag-pipeline` | RAG PostgreSQL + nomic-embed-text + fallback browser + keyword matching |
| `/docker-infrastructure` | Docker multi-stage + Compose Node+PostgreSQL+Ollama |
| `/playwright-e2e` | Tests E2E con webServer config, API tests, localStorage injection |
| `/pdf-export-frontend` | html2canvas + jsPDF lazy-loaded, scale:2, multipage |

## Skills — Google Cloud / GenAI (ML)

| Skill | Uso |
| --- | --- |
| `/vertex-ai` | Vertex AI, Gemini API, Model Garden, Vector Search, RAG Engine, Agent Builder, labs skills.google (`skills/vertex-ai/`) |

## Skills — Datos y análisis

| Skill | Uso |
| --- | --- |
| `/csv-analyst` | CSVs masivos pandas — SECOP, persona natural CC, montos COP |
| `/secop-socrata` | Socrata SODA API datos.gov.co — IDs datasets, queries SOQL |
| `/forensic-analysis` | Motor de riesgo forense: bunching, similitud semántica, scoring Red/Orange/Green |
| `/multiagent` | Agentes paralelos — tipos, cuándo usarlos, prompts autocontenidos |

## Skills — IA, agentes y certificación Anthropic

| Skill | Uso |
| --- | --- |
| `/agentic-workflows` | ReAct, Plan-and-Execute, self-reflection, orquestación multi-agente local (`skills/agentic-workflows/`) |
| `/anthropic-architect` | Claude Certified Architect: Agent SDK, tool use, MCP, Claude Code en equipos (`skills/anthropic-architect/`) |

## Skills — Inversión (Rutan / LATAM)

| Skill | Uso |
| --- | --- |
| `/venture-investor` | Investor Academy Rutan — ángel y VC, ecosistema COL/LATAM (`skills/venture-investor/`) |
| `/lanchmon-rutan` | Portal Lanchmon iNNpulsa — academy, bots IA (valuation, pitch, market size) (`skills/lanchmon-rutan/`) |

## Skills — Web3 / hackathon

| Skill | Uso |
| --- | --- |
| `/solana-hackathon` | Colosseum Frontier, stack Solana, track IA Agents, recursos RPC (`skills/solana-hackathon/`) |

## Skills — Cloud & Seguridad

| Skill | Uso |
| --- | --- |
| `/google-cloud-cybersecurity` | GCP Security: IAM, SCC, NIST CSF, Incident Response, DevSecOps, GenAI en security (apuntes extensos: `skills/google-cloud-cybersecurity/course_notes_full.md`) |
| `/cybersec-defense-stack` | **MAESTRO** defense-in-depth 8 layers + NIST CSF + IR playbook + presentación evidencia |
| `/cybersec-ec-council-ceh` | CEH v13 — 5 fases ataque + 20 módulos + reporting estilo CEH |
| `/cybersec-ridgebot` | Automated pentest AI · MITRE ATT&CK · Botlets · continuous testing |
| `/cybersec-pentera` | ASV · CTEM 5 stages · BAS 2.0 · adversarial autonomo en producción |
| `/cybersec-picus` | BAS · micro-emulation MITRE · SIEM/EDR gap analysis · detection rules |
| `/cybersec-palo-alto-cortex` | XSIAM unificado (SIEM+SOAR+XDR+UEBA+ASM) + Prisma Cloud CNAPP |
| `/cybersec-fortinet-fabric` | Security Fabric (NGFW + EDR + Analyzer + SOAR) + hardening best practices |
| `/cybersec-radware` | Cloud WAF + DDoS app-layer + Bot Management + API protection |
| `/cyber-attacks-defense` | OWASP Top 10 vistos desde blue team: inyección, XSS, CSRF, broken access control + defensa en profundidad (`skills/skill_cyber_attacks_defense.md`) |

## Skills — Lab10 (programa AI Builders)

| Skill | Uso |
| --- | --- |
| `/lab10-reto-agentes` | 13 módulos programa Reto Agentes (master) |
| `/lab10-talleres-yt` | 21 talleres oficiales YouTube canal Truora |
| `/lab10-rag` | Consulta semántica sobre todo (227 chunks · grep transcripts) |
| `/lab10-openclaw-101` | Filosofía OpenClaw · lanzamiento nov-2025 · open source |
| `/lab10-skill-anatomy` | Estructura SKILL.md · frontmatter · detección por LLM |
| `/lab10-tools-vs-skills` | Día 4 Reto · diferencias claras tools (determinista) vs skills (instrucciones) |
| `/lab10-agent-autonomy` | Día 7 Reto · heartbeat · crons · autonomía sin supervisión |
| `/lab10-agent-projects-estudiantes` | Ejemplos reales agentes construidos por estudiantes |

## Skills — Scraping y descarga

| Skill | Uso |
| --- | --- |
| `/site-cloner` | Clonar membership areas (ClickFunnels/Kajabi/Teachable) — login anti-bot, scrape, assets, build React |
| `/hls-video-downloader` | Descargar HLS m3u8 de Vidalytics/Vimeo/Wistia/Bunny.net con Playwright + yt-dlp |
| `/react-course-player` | LMS player React responsive — sidebar, video/audio local, sessionStorage progress, dark theme |

## Skills — Deployment y publicación

| Skill | Uso |
| --- | --- |
| `/tunnel-manager` | Cloudflare tunnels — proteger URL, watchdog, restart seguro, NUNCA matar cloudflared |
| `/hackathon-dashboard` | React dashboard tabs, QCard/BigAnswer, Recharts, publicación tunnel |

## Skills — Metadoc Jarvis (evolución del repo)

| Skill | Uso |
| --- | --- |
| `/meta-workflow` | Tras tareas relevantes: nuevo skill en `skills/`, actualizar `memory/MEMORY.md`, re-ejecutar ingest RAG (`skills/skill_meta_workflow.md`) |

## Skills — OdooFactory (proyecto específico)

Comandos habituales en el repo OdooFactory (no hay carpeta equivalente en este repo): `/odoo-check` `/odoo-deploy` `/odoo-tunnel`

# Jarvis — IA Local Auto-Constructible

> Un asistente de IA local que se instala solo, contiene todo el conocimiento adquirido y reemplaza Claude/ChatGPT sin suscripciones.

## Instalación en máquina nueva

### Windows
```powershell
git clone https://github.com/rafaelcastro/jarvis
cd jarvis
.\setup.ps1
```

### Linux/Mac
```bash
git clone https://github.com/rafaelcastro/jarvis
cd jarvis
chmod +x setup.sh && ./setup.sh
```

El script instala todo: Python, Playwright, Ollama, modelos, OpenWebUI, y configura los skills de Claude Code.

---

## Stack

| Componente | Tecnología | Puerto |
|------------|-----------|--------|
| Chat UI (ChatGPT local) | OpenWebUI + Ollama | 3000 |
| Coding assistant (Claude Code local) | Aider + qwen2.5-coder | CLI |
| RAG (documentos propios) | AnythingLLM + nomic-embed-text | 3001 |
| Modelo principal | qwen3:8b | 11434 |
| Modelo código | qwen2.5-coder:7b | 11434 |
| Embeddings | nomic-embed-text | 11434 |

## Estructura
```
jarvis/
├── setup.ps1              # Setup automático Windows
├── setup.sh               # Setup automático Linux/Mac
├── docker-compose.yml     # OpenWebUI + AnythingLLM
├── skills/                # Todos los Claude Code skills
│   ├── anthropic-architect/
│   ├── site-cloner/
│   ├── ollama-local/
│   ├── hls-video-downloader/
│   ├── react-course-player/
│   └── google-cloud-cybersecurity/
├── knowledge/             # Base de conocimiento para RAG
│   ├── anthropic_academy/ # Cursos Anthropic completados
│   └── scraping/          # Técnicas validadas de scraping
├── scripts/               # Scripts de automatización Playwright
│   ├── smart_quiz.py      # Quiz solver Skilljar
│   ├── save_certs.py      # Descarga certificados
│   └── ...
└── src/                   # Núcleo de Jarvis
    ├── jarvis.py          # CLI principal
    ├── rag/               # Pipeline RAG con Ollama
    └── tools/             # Herramientas MCP locales
```

## Certificaciones obtenidas (2026-05-11)

| Curso | Lecciones | Certificado |
|-------|-----------|-------------|
| Building with the Claude API | 85/85 | https://verify.skilljar.com/c/pm37tgsa25cs |
| Introduction to MCP | 14/14 | https://verify.skilljar.com/c/y7nxsogtbk59 |
| Claude Code in Action | 21/21 | https://verify.skilljar.com/c/yvy7twu3ainb |
| Claude 101 | 14/14 | https://verify.skilljar.com/c/xkaer8c2j5th |

## Próximo paso
- Examen Claude Certified Architect ($99, proctored): aplicar en claude.com/partners primero

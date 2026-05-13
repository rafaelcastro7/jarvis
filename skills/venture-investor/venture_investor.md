# Venture Investor Academy — Rutan/iNNpulsa Colombia

## Acceso local
- Servidor: http://localhost:3055
- Sección: Venture School (Rutan)
- API metadata: GET /api/metadata → rutan.*
- API videos: GET /api/venture/videos
- API bots: POST /api/venture/chat {botId, message, history}

## Módulos del curso (7 módulos)
- **Módulo 0 — Punto de partida** (5 videos): Punto de partida: bienvenida, roles, oportunidades, portafolio, frontera eficiente e introducción al Venture Capital.
- **Módulo 1 — Introducción al Venture Capital** (6 videos): Fundamentos del Venture Capital: qué es, criterios y tesis de inversión, dinámica (Curva J y Power Law) y tipos de salid
- **Módulo 2 — Estructura y Procesos de un Fondo VC** (8 videos): Estructura y operación de un fondo VC: actores del ecosistema, roles GP/LP, ciclo de vida, y procesos clave como Capital
- **Módulo 3 — Estado y Dinámicas del VC** (4 videos): Estado y dinámicas del VC: inversión y fundraising global, tendencias en LatAm, panorama de salidas/retornos y situación
- **Módulo 4 y 5 — Instrumentos de Inversión y Análisis** (7 videos): Instrumentos de inversión: estructuras comunes, lógica económica, análisis de posiciones, preferencias, protecciones, es
- **Módulo 6 — Creación de una Tesis de Inversión** (5 videos): Creación de una tesis de inversión: el porqué, pilares técnicos, value stack, generación de valor y redacción práctica.
- **Módulo 7 — Valoración de Startups** (7 videos): Valoración de startups: retos, métodos (DCF, Scorecard, Comparables, VC Method) aplicados al Venture Capital.

## Lecciones con video (5 videos — Google Drive embeds)
- Módulo 0 / Bienvenida → Drive:1CG87g6uyqE0perKC-VJywIT4-OTQucJb
- Módulo 0 / Auto Identificación de roles y oportunidades → Drive:1f4G44hg2LW32tgmMpTEoYeA2GpjZN3yy
- Módulo 0 / La inversión como catalizador de innovación → Drive:1FJMwgaMGrXFX_rl1z8XmCjzpPPqK4MDf
- Módulo 0 / Construcción de portafolio y frontera eficiente → Drive:1kAOsQf1Qk51DAVF5Gn0-pCwHvrqQce2s
- Módulo 0 / Cierre y bienvenida al Venture Capital → Drive:124gHr5SbB0a45wq2AcTwUH00Rv1Ulsxo

## Bots IA locales (Ollama qwen3:4b)


## Glosario (primeros 20 términos)


## Recursos PDF (0 recursos)
Descargados en: downloads/lanchmon_full/resources/
Accesibles en: /downloads/lanchmon_full/resources/<filename>

## RAG
Chunks indexados: rag/venture_chunks.jsonl
Para buscar: cargar JSONL, calcular cosine similarity con nomic-embed-text

## Scripts útiles
- `scripts/lanchmon_extract_videos.py` — extrae Drive IDs de todas las lecciones
- `scripts/ingest_venture_rag.py` — re-indexa contenido al RAG
- `scripts/build_rutan_metadata.py` — actualiza consolidated_metadata.json

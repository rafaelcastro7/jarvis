---
name: lab10-rag
description: Consulta semantica sobre el contenido completo de Lab10 (49 videos descargados). Usa grep en transcripts para encontrar temas especificos. Cubre Reto Agentes (13 modulos) + Talleres YT (21 videos).
---

# Lab10 RAG - Consulta semantica

## Quick search

```bash
# Buscar termino en todos los transcripts
grep -l "termino" E:\Documents\PROYECTOS\AgencIA\lab10-clone\transcripts*/*.txt

# Con contexto
grep -i -B2 -A5 "RAG" E:\Documents\PROYECTOS\AgencIA\lab10-clone\transcripts_yt/*.txt
```

## Chunks JSONL

`E:\Documents\PROYECTOS\AgencIA\lab10-clone\rag\lab10_chunks.jsonl` — 227 chunks
Cada linea: `{"source": "lms/xxx", "video_id": "xxx", "text": "..."}`

## Como hacer query semantica (Ollama)

```python
import json
from pathlib import Path
import requests

OLLAMA = "http://localhost:11434"
chunks = [json.loads(l) for l in Path(r"E:\Documents\PROYECTOS\AgencIA\lab10-clone\rag\lab10_chunks.jsonl").open(encoding='utf-8')]

def embed(text):
    r = requests.post(f"{OLLAMA}/api/embeddings", json={"model":"nomic-embed-text","prompt":text})
    return r.json()['embedding']

# Buscar
q_emb = embed("como creo una skill")
# Comparar con chunks (necesitas pre-computar)
```

## Cobertura

- Reto Agentes: 27 videos transcritos
- Talleres YT: 1 videos transcritos
- Total chunks: 227

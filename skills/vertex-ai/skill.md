---
name: vertex-ai
description: Google Cloud Vertex AI — labs gratuitos en skills.google.com, Gemini API, Model Garden, Vector Search, RAG Engine, Agent Builder. Stack completo para reemplazar OpenAI con Google Cloud. Includes Python SDK, streaming, multimodal, embeddings, fine-tuning y deployment.
tools: Bash, Read, Write, Edit, WebFetch, WebSearch
---

# Vertex AI — Google Cloud IA

## Acceso a Labs Gratuitos

```
URL: https://skills.google.com → buscar "Vertex AI"
Cuenta: Google Account (no requiere tarjeta de crédito para labs)
Labs: corren en entorno Google Cloud preconfigurado — 0 costo
Duración típica: 30-90 min por lab
```

**Paths recomendados en skills.google:**
- "Develop GenAI Apps with Gemini and Streamlit" — lab práctico completo
- "Prompt Design in Vertex AI" — fundamentos + few-shot + chain-of-thought
- "Vertex AI: Qwik Start" — primer lab, 30 min
- "Build and Deploy Machine Learning Solutions on Vertex AI" — path completo

---

## Gemini API desde Python (equivalente a Claude API)

```python
# pip install google-cloud-aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel, Part

vertexai.init(project="TU_PROJECT_ID", location="us-central1")

model = GenerativeModel("gemini-1.5-pro")

# Chat simple
response = model.generate_content("Explica clean architecture en 3 puntos")
print(response.text)

# Streaming
for chunk in model.generate_content("Escribe un componente React", stream=True):
    print(chunk.text, end="", flush=True)

# Multimodal (imagen + texto)
image = Part.from_uri("gs://mi-bucket/imagen.jpg", mime_type="image/jpeg")
response = model.generate_content([image, "¿Qué hay en esta imagen?"])
```

---

## Gemini con Tool Use (equivalente a Claude tool_use)

```python
from vertexai.generative_models import (
    GenerativeModel, Tool, FunctionDeclaration, AutomaticFunctionCallingResponder
)

# Definir herramientas
get_weather = FunctionDeclaration(
    name="get_weather",
    description="Obtiene el clima actual de una ciudad",
    parameters={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "Nombre de la ciudad"},
        },
        "required": ["city"],
    },
)

weather_tool = Tool(function_declarations=[get_weather])

model = GenerativeModel("gemini-1.5-pro", tools=[weather_tool])
chat = model.start_chat()

response = chat.send_message("¿Qué clima hace en Bogotá?")

# Manejar tool calls
for part in response.candidates[0].content.parts:
    if part.function_call:
        fc = part.function_call
        print(f"Tool: {fc.name}, Args: {dict(fc.args)}")
        # Ejecutar la función y devolver resultado
        result = execute_function(fc.name, dict(fc.args))
        response = chat.send_message(
            Part.from_function_response(name=fc.name, response={"result": result})
        )
```

---

## Embeddings con Vertex AI

```python
from vertexai.language_models import TextEmbeddingModel

model = TextEmbeddingModel.from_pretrained("text-embedding-004")

# Embed un texto
embeddings = model.get_embeddings(["Texto a vectorizar"])
vector = embeddings[0].values  # Lista de 768 floats

# Embed múltiples textos (batch)
texts = ["Documento 1", "Documento 2", "Documento 3"]
embeddings = model.get_embeddings(texts)
vectors = [e.values for e in embeddings]
```

---

## RAG Engine (RAG gestionado por Google)

```python
from vertexai.preview import rag
import vertexai

vertexai.init(project="TU_PROJECT", location="us-central1")

# Crear corpus RAG
corpus = rag.create_corpus(display_name="mi-knowledge-base")

# Importar documentos desde GCS
rag.import_files(
    corpus.name,
    paths=["gs://mi-bucket/documentos/"],
    chunk_size=512,
    chunk_overlap=100,
)

# Query RAG
response = rag.retrieval_query(
    rag_resources=[rag.RagResource(rag_corpus=corpus.name)],
    text="¿Cómo funciona el agentic loop?",
    similarity_top_k=5,
)

for context in response.contexts.contexts:
    print(f"Score: {context.score:.3f}")
    print(context.text[:200])
```

---

## Agent Builder (agentes con Vertex AI)

```python
from google.cloud import dialogflow_cx_v3 as dialogflow

# Vertex AI Agent Builder = Dialogflow CX + Gemini backend
# Alternativa: usar directamente el SDK de agentes

from vertexai.preview.reasoning_engines import ReasoningEngine

# Definir agente
class MiAgente:
    def query(self, input: str) -> str:
        model = GenerativeModel("gemini-1.5-pro")
        return model.generate_content(input).text

# Deploy en Vertex AI (managed)
agent = ReasoningEngine.create(
    MiAgente(),
    requirements=["google-cloud-aiplatform"],
    display_name="mi-agente",
)

# Invocar
response = agent.query(input="¿Qué es el MCP protocol?")
```

---

## Model Garden — Modelos disponibles gratis

| Modelo | Uso | Gratis en labs |
|--------|-----|---------------|
| `gemini-1.5-pro` | Chat, reasoning, multimodal | ✅ |
| `gemini-1.5-flash` | Rápido y barato | ✅ |
| `gemini-2.0-flash` | Más nuevo, rápido | ✅ |
| `text-embedding-004` | Embeddings 768d | ✅ |
| `imagegeneration@006` | Imágenes (Imagen 3) | ✅ en labs |
| `Llama 3.1` | Open source en Vertex | ✅ en labs |
| `Claude 3.5 Sonnet` | Via Vertex Model Garden | 💰 pago |

---

## Comparativa Vertex AI vs Claude API

| Feature | Vertex AI (Gemini) | Claude API (Anthropic) |
|---------|-------------------|----------------------|
| Precio por 1M tokens | $0.075-$3.50 | $3-$15 |
| Context window | 1M tokens | 200K tokens |
| Multimodal | ✅ texto+imagen+video+audio | ✅ texto+imagen |
| Tool use | ✅ | ✅ |
| Batch API | ✅ | ✅ |
| RAG gestionado | ✅ RAG Engine | ❌ (DIY) |
| Gratis para labs | ✅ skills.google.com | ❌ |
| Free tier | $300 créditos nuevos | ❌ |

---

## Setup rápido local

```bash
# 1. Instalar SDK
pip install google-cloud-aiplatform

# 2. Autenticación
gcloud auth application-default login
# O con service account:
export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"

# 3. Configurar proyecto
gcloud config set project TU_PROJECT_ID
gcloud services enable aiplatform.googleapis.com

# 4. Test rápido
python -c "
import vertexai
from vertexai.generative_models import GenerativeModel
vertexai.init(project='TU_PROJECT', location='us-central1')
print(GenerativeModel('gemini-1.5-flash').generate_content('Hola').text)
"
```

---

## Precios reales (2025)

| Modelo | Input | Output |
|--------|-------|--------|
| Gemini 1.5 Flash | $0.075/1M | $0.30/1M |
| Gemini 1.5 Pro | $1.25/1M | $5.00/1M |
| Gemini 2.0 Flash | $0.10/1M | $0.40/1M |
| text-embedding-004 | $0.00002/1K | — |

**Free tier:** $300 USD en créditos GCP para cuentas nuevas (90 días).
**Labs:** 100% gratis en skills.google.com — entorno Qwiklabs preconfigurado.

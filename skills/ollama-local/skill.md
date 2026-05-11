---
name: ollama-local
description: Gestión completa de Ollama local — instalación, modelos recomendados, cliente con retry y caché de embeddings, NO_THINK prefix, fallback chain de modelos, y diagnóstico. Stack usado en GobIA Auditor (Node 24 + Windows 11). Incluye stack completo para reemplazar Claude/ChatGPT con IA local gratuita.
tools: Bash, PowerShell, Read, Edit
---

# Ollama Local — Gestión y Cliente

## Instalación y modelos base

```powershell
# Descargar desde https://ollama.com (Windows installer)
# Después de instalar:

ollama pull nomic-embed-text   # Embeddings 768d — REQUERIDO para RAG
ollama pull qwen3:4b           # Generación principal (2.5 GB)
ollama pull tinyllama          # Fallback mínimo (637 MB) — tests y E2E

# Opcionales (más calidad, más VRAM)
ollama pull gemma4-fast        # Alta calidad (9.6 GB)
ollama pull qwen2.5-coder:7b   # Para código
```

---

## Estado y diagnóstico

```powershell
# Verificar que Ollama corre
ollama list                    # Modelos instalados
ollama ps                      # Modelos cargados en memoria

# Test rápido
ollama run tinyllama "Di solo: OK"

# Verificar API directamente
Invoke-WebRequest "http://localhost:11434/api/tags" -UseBasicParsing | Select-Object -ExpandProperty Content

# Desde Node
curl http://localhost:11434/api/tags
```

---

## Cliente con timeout (src/server/ollama.ts)

```typescript
import { config } from "./config";

interface OllamaGenerateResponse { response?: string; }
interface OllamaEmbeddingResponse { embedding: number[]; }

export async function callOllama<T>(endpoint: string, payload: unknown): Promise<T> {
  // CRÍTICO: endpoint DEBE empezar con /api/
  // ✅ callOllama("/api/generate", ...)
  // ❌ callOllama("generate", ...) → URL queda "http://localhost:11434generate"
  
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), config.ollamaTimeoutMs);
  
  try {
    const response = await fetch(`${config.ollamaHost}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error(`Ollama ${response.status}: ${await response.text()}`);
    }
    return response.json() as Promise<T>;
  } finally {
    clearTimeout(timeout);
  }
}

export async function getEmbedding(model: string, text: string): Promise<number[]> {
  const result = await callOllama<OllamaEmbeddingResponse>("/api/embeddings", {
    model, prompt: text,
  });
  return result.embedding;
}
```

---

## Cliente frontend con retry + caché (src/lib/gemini.ts)

```typescript
const GENERATE_MODELS = ["qwen3:4b", "gemma4-fast:latest", "tinyllama:latest"];
const EMBED_MODEL = "nomic-embed-text";
const NO_THINK_PREFIX = "/no_think\n";

// Caché de embeddings en memoria (evita re-embedear textos repetidos)
const embeddingCache = new Map<string, number[]>();

// withRetry — exponential backoff
async function withRetry<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  let delay = 2000;
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxRetries - 1) throw error;
      const jitter = Math.random() * 2000;
      console.warn(`[Ollama] Intento ${attempt + 1} fallido, reintentando en ${Math.round((delay + jitter) / 1000)}s`);
      await new Promise((r) => setTimeout(r, delay + jitter));
      delay *= 2;
    }
  }
  throw new Error("Max retries exceeded");
}

// Generación con fallback entre modelos
async function generateText(prompt: string, numPredict = 400): Promise<string> {
  for (const model of GENERATE_MODELS) {
    try {
      const response = await withRetry(() =>
        callLocalModel<{ response?: string }>("generate", {
          model,
          prompt: `${NO_THINK_PREFIX}${prompt}`,
          stream: false,
          options: { num_predict: numPredict, temperature: 0.2 },
        })
      );
      const text = response.response?.trim() || "";
      if (text) return text;
    } catch {
      console.warn(`[Ollama] Modelo ${model} falló, probando siguiente`);
    }
  }
  return "";  // Todos fallaron → el llamador usa fallback determinístico
}

// Embeddings con caché
export async function getEmbedding(text: string): Promise<number[]> {
  if (embeddingCache.has(text)) return embeddingCache.get(text)!;
  
  try {
    const result = await withRetry(() =>
      callLocalModel<{ embedding: number[] }>("embeddings", {
        model: EMBED_MODEL,
        prompt: text,
      })
    );
    embeddingCache.set(text, result.embedding);
    return result.embedding;
  } catch {
    return new Array(768).fill(0);  // Vector cero como fallback
  }
}
```

---

## NO_THINK prefix

Los modelos como `qwen3:4b` tienen modo "thinking" que genera tokens de razonamiento interno antes de la respuesta. Esto aumenta la latencia y el uso de tokens.

```typescript
// Deshabilitar thinking — respuesta directa y más rápida
const prompt = `/no_think\n${userPrompt}`;

// Con thinking habilitado (por defecto)
const prompt = userPrompt;
```

Usar `/no_think` para:
- Chat en tiempo real (latencia < 3s)
- Embeddings / clasificación
- Respuestas cortas y directas

No usar `/no_think` para:
- Análisis forense complejo
- Generación de reportes largos
- Razonamiento multi-paso

---

## Endpoints Ollama API

| Endpoint | Método | Uso |
|----------|--------|-----|
| `/api/generate` | POST | Generación de texto |
| `/api/embeddings` | POST | Vectorización de texto |
| `/api/tags` | GET | Modelos instalados |
| `/api/show` | POST | Info de un modelo |
| `/api/pull` | POST | Descargar modelo |
| `/api/ps` | GET | Modelos en memoria |

---

## Payloads

```typescript
// Generación
{
  model: "qwen3:4b",
  prompt: "/no_think\nTu prompt aquí",
  stream: false,
  options: {
    num_predict: 500,    // Máximo tokens a generar
    temperature: 0.3,    // 0 = determinístico, 1 = creativo
  }
}

// Embeddings
{
  model: "nomic-embed-text",
  prompt: "Texto a vectorizar"
}
```

---

## Modelos y su uso recomendado

| Modelo | VRAM | Velocidad | Mejor para |
|--------|------|-----------|-----------|
| `tinyllama` | ~1 GB | Muy rápido | Tests, E2E, respuestas simples |
| `qwen3:4b` | ~3 GB | Rápido | Chat, análisis, producción |
| `gemma4-fast` | ~10 GB | Medio | Alta calidad cuando hay VRAM |
| `nomic-embed-text` | ~0.3 GB | Muy rápido | Embeddings RAG — siempre activo |

**Hardware mínimo:** 8 GB RAM + GPU 4 GB VRAM (NVIDIA GTX 1060+)
**Hardware recomendado:** 16 GB RAM + GPU 8 GB VRAM (NVIDIA GTX 1070+)

---

## Proxy en Express (evita CORS del frontend)

```typescript
// POST /api/ollama/generate → proxy a Ollama local
app.post("/api/ollama/generate", asyncHandler(async (req, res) => {
  const { model, prompt, stream = false, options = {} } = req.body;
  const result = await callOllama<{ response?: string }>("/api/generate", {
    model, prompt: `/no_think\n${prompt}`, stream, options,
  });
  res.json({ response: result.response });
}));

// POST /api/ollama/embeddings → proxy a Ollama embeddings
app.post("/api/ollama/embeddings", asyncHandler(async (req, res) => {
  const { model, prompt } = req.body;
  const result = await callOllama<{ embedding: number[] }>("/api/embeddings", {
    model, prompt,
  });
  res.json({ embedding: result.embedding });
}));
```

---

## Troubleshooting

| Síntoma | Causa | Fix |
|---------|-------|-----|
| `connection refused :11434` | Ollama no está corriendo | `ollama serve` en terminal |
| URL `http://localhost:11434generate` | Falta `/api/` en endpoint | `callOllama("/api/generate", ...)` |
| Timeout en embeddings | Modelo no cargado | `ollama run nomic-embed-text "test"` para precalentar |
| Respuesta vacía | `num_predict` muy bajo | Aumentar a 200-500 |
| Thinking tokens en respuesta | `/no_think` no aplicado | Agregar prefix al prompt |

---

## Stack completo para reemplazar Claude/ChatGPT (OBJETIVO PRINCIPAL)

### Herramientas gratuitas equivalentes

| Herramienta paga | Reemplazo gratuito local | Instalación |
|-----------------|--------------------------|-------------|
| Claude.ai / ChatGPT | **OpenWebUI** + Ollama | `docker run -p 3000:8080 ghcr.io/open-webui/open-webui` |
| Claude API | **Ollama API** en `localhost:11434` | API compatible con OpenAI |
| Claude Code CLI | **Aider** + qwen2.5-coder | `pip install aider-chat` |
| Cursor IDE | **Continue.dev** extension VSCode | Open source, usa Ollama |
| Perplexity / RAG | **AnythingLLM** | Docker o instalador Windows |
| GitHub Copilot | **Tabby** o **Continue** | Ambos usan modelos locales |

### Setup rápido OpenWebUI (interfaz tipo ChatGPT)
```powershell
# Con Docker
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway `
  -v open-webui:/app/backend/data `
  --name open-webui ghcr.io/open-webui/open-webui:main

# Acceder en http://localhost:3000
# Conecta automáticamente con Ollama en host.docker.internal:11434
```

### Setup Aider (coding assistant como Claude Code)
```powershell
pip install aider-chat

# Usar con modelo local
aider --model ollama/qwen2.5-coder:7b --no-auto-commits

# Configurar en .env
$env:OLLAMA_API_BASE = "http://localhost:11434"
```

### Modelos recomendados para reemplazar Claude

| Tarea | Modelo | Tamaño | Comando |
|-------|--------|--------|---------|
| Chat general | `qwen3:8b` | 5 GB | `ollama pull qwen3:8b` |
| Código | `qwen2.5-coder:7b` | 4.7 GB | `ollama pull qwen2.5-coder:7b` |
| Razonamiento | `deepseek-r1:7b` | 4.7 GB | `ollama pull deepseek-r1:7b` |
| Rápido/móvil | `qwen3:4b` | 2.5 GB | `ollama pull qwen3:4b` |
| Embeddings RAG | `nomic-embed-text` | 274 MB | `ollama pull nomic-embed-text` |

### AnythingLLM — RAG sobre documentos propios
```powershell
# Instalar desde https://anythingllm.com/
# Configurar: Settings → LLM Provider → Ollama → http://localhost:11434
# Subir PDFs/TXTs de los cursos de Platzi → chat con el contenido
```

### Usar la API de Ollama como si fuera OpenAI
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # requerido pero ignorado
)

response = client.chat.completions.create(
    model="qwen3:4b",
    messages=[{"role": "user", "content": "Explica clean architecture"}]
)
print(response.choices[0].message.content)
```

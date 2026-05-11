---
name: rag-pipeline
description: Pipeline RAG completo con Ollama (nomic-embed-text), PostgreSQL para persistencia, fallback a RAG local en browser y keyword matching. Implementado en GobIA Auditor para base de conocimiento jurídico (49 referencias).
tools: Read, Edit, Write, Bash
---

# RAG Pipeline — Persistente con Ollama + PostgreSQL

## Arquitectura de 3 niveles

```
getLegalContext(query, redFlags)
        │
        ├─ 1. RAG Servidor (PostgreSQL + nomic-embed-text)  ← ideal
        │      ├─ Indexar KB en legal_context_cache
        │      ├─ Embed query → cosine similarity
        │      └─ Top-3 filtrado > 0.35
        │
        ├─ 2. RAG Local Browser (mismos embeddings, sin DB)  ← fallback
        │      ├─ Carga embeddings en memoria
        │      └─ Race con timeout de 2s
        │
        └─ 3. Keyword Matching (sin embeddings)             ← emergencia
               ├─ Token splitting
               └─ Bonus por red flags conocidas
```

---

## Esquema PostgreSQL

```sql
CREATE TABLE IF NOT EXISTS legal_context_cache (
  id         TEXT PRIMARY KEY,
  source     TEXT NOT NULL,
  text       TEXT NOT NULL,
  embedding  DOUBLE PRECISION[] NOT NULL,
  updated_at BIGINT NOT NULL
);
```

---

## Backend: `src/server/rag.ts`

```typescript
import { getEmbedding } from "./ollama";
import { cosineSimilarity } from "../lib/vector";
import { LEGAL_KNOWLEDGE_BASE } from "../lib/legalKnowledgeBase";
import { query as dbQuery } from "./database";

const EMBED_MODEL = "nomic-embed-text";

// Indexar toda la base de conocimiento (solo si no está indexada)
async function ensureLegalContextIndex() {
  for (const item of LEGAL_KNOWLEDGE_BASE) {
    const { rows } = await dbQuery(
      "SELECT id FROM legal_context_cache WHERE id = $1",
      [item.id]
    );
    if (rows.length === 0) {
      const embedding = await getEmbedding(EMBED_MODEL, `${item.source}: ${item.text}`);
      await dbQuery(
        `INSERT INTO legal_context_cache (id, source, text, embedding, updated_at)
         VALUES ($1, $2, $3, $4, $5)
         ON CONFLICT (id) DO UPDATE SET embedding=$4, updated_at=$5`,
        [item.id, item.source, item.text, JSON.stringify(embedding), Date.now()]
      );
    }
  }
}

export async function getPersistentLegalContext(
  query: string,
  redFlags: string[] = []
): Promise<string> {
  await ensureLegalContextIndex();
  const queryEmbedding = await getEmbedding(EMBED_MODEL, query);

  const { rows } = await dbQuery<{
    id: string; source: string; text: string; embedding: string;
  }>("SELECT id, source, text, embedding FROM legal_context_cache", []);

  const ranked = rows
    .map((row) => {
      const emb = typeof row.embedding === "string"
        ? JSON.parse(row.embedding) as number[]
        : (row.embedding as unknown as number[]);
      return {
        ...row,
        score: cosineSimilarity(queryEmbedding, emb) + relevanceBonus(row.text, redFlags),
      };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)
    .filter((item) => item.score > 0.35);

  if (ranked.length === 0) return "";

  return ranked
    .map((item) =>
      `### ${item.source}\n${item.text}\n(Relevancia: ${(item.score * 100).toFixed(1)}%)`
    )
    .join("\n\n---\n\n");
}

function relevanceBonus(text: string, redFlags: string[]): number {
  let bonus = 0;
  const t = text.toLowerCase();
  if (redFlags.some((f) => f.includes("fraccionamiento")) && t.includes("fraccionamiento")) bonus += 0.2;
  if (redFlags.some((f) => f.includes("bunching")) && t.includes("adjudicac")) bonus += 0.3;
  if (redFlags.some((f) => f.includes("directa")) && t.includes("directa")) bonus += 0.2;
  return bonus;
}
```

---

## Frontend: `src/lib/ragManager.ts`

```typescript
export async function getLegalContext(query: string, redFlags: string[] = []): Promise<string> {
  // Nivel 1: servidor
  try {
    const response = await fetch("/api/rag/legal-context", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, redFlags }),
      signal: AbortSignal.timeout(5000),
    });
    if (response.ok) {
      const payload = await response.json();
      if (typeof payload.context === "string" && payload.context.length > 10) {
        return payload.context;
      }
    }
  } catch { /* fall through */ }

  // Nivel 2: RAG local con race vs timeout
  try {
    return await Promise.race<string>([
      getLocalLegalContext(query, redFlags),
      new Promise<string>((resolve) =>
        setTimeout(() => resolve(getQuickLegalContext(query, redFlags)), 2000)
      ),
    ]);
  } catch {
    return getQuickLegalContext(query, redFlags);
  }
}

// Nivel 3: keyword matching sin embeddings
function getQuickLegalContext(query: string, redFlags: string[]): string {
  const terms = `${query} ${redFlags.join(" ")}`.toLowerCase().split(/\s+/).filter(Boolean);
  return LEGAL_KNOWLEDGE_BASE
    .map((item) => {
      const content = `${item.source} ${item.text}`.toLowerCase();
      const score = terms.reduce((acc, t) => acc + (content.includes(t) ? 1 : 0), 0);
      return { ...item, score };
    })
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)
    .map((item) => `### ${item.source}\n${item.text}`)
    .join("\n\n---\n\n");
}
```

---

## Endpoint Express

```typescript
app.post("/api/rag/legal-context", asyncHandler(async (req, res) => {
  const { query, redFlags = [] } = req.body;
  const context = await getPersistentLegalContext(String(query), redFlags as string[]);
  res.json({ context });
}));
```

---

## Estructura de la base de conocimiento

```typescript
// src/lib/legalKnowledgeBase.ts
export interface LegalContext {
  id: string;       // e.g. "ley-80-art-24-25"
  source: string;   // e.g. "Ley 80 de 1993, Artículo 24"
  text: string;     // descripción detallada del artículo/norma
  embedding?: number[]; // pre-computado si se quiere
}

export const LEGAL_KNOWLEDGE_BASE: LegalContext[] = [
  {
    id: "ley-80-art-24-25",
    source: "Ley 80 de 1993, Artículos 24 y 25",
    text: "El fraccionamiento de contratos ocurre cuando una entidad estatal divide...",
  },
  // ... 49 total en GobIA
];
```

---

## Cosine Similarity: `src/lib/vector.ts`

```typescript
export function cosineSimilarity(a: number[], b: number[]): number {
  if (!a?.length || a.length !== b?.length) return 0;
  let dot = 0, magA = 0, magB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    magA += a[i] * a[i];
    magB += b[i] * b[i];
  }
  if (magA === 0 || magB === 0) return 0;
  return dot / (Math.sqrt(magA) * Math.sqrt(magB));
}
```

---

## Modelo de embeddings

| Modelo | Dimensiones | Instalación |
|--------|------------|-------------|
| `nomic-embed-text` | 768 | `ollama pull nomic-embed-text` |
| `mxbai-embed-large` | 1024 | Alternativa más precisa |

**Endpoint Ollama:** `POST /api/embeddings` con `{ model, prompt }`

---

## Umbral de relevancia

- `score > 0.35` → incluir en contexto
- `score > 0.7` → alta relevancia, mostrar primero
- Bonus máximo por red flags: `+0.3`
- Siempre top-3 máximo para no saturar el contexto del LLM

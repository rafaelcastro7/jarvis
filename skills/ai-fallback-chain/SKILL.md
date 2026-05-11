---
name: ai-fallback-chain
description: Cadena de fallback Claude → Gemini → Ollama local para endpoints de chat/generación. Probado en producción en GobIA Auditor. Incluye manejo de timeout, provider tracking y respuesta de emergencia.
tools: Read, Edit, Bash
---

# AI Fallback Chain — Claude → Gemini → Ollama

## Patrón probado en producción (`src/server/app.ts`)

```typescript
POST /api/chat/assistant
body: { systemPrompt: string, userMessage: string, history?: {role,content}[] }
```

### Implementación completa

```typescript
app.post("/api/chat/assistant", asyncHandler(async (req, res) => {
  const { systemPrompt, userMessage, history = [] } = req.body;

  const messages = [
    ...history.slice(-8).map((m: { role: string; content: string }) => ({
      role: m.role as "user" | "assistant",
      content: m.content,
    })),
    { role: "user" as const, content: userMessage },
  ];

  // ── 1. Claude Haiku ──────────────────────────────────────────────────────
  if (config.anthropicApiKey) {
    try {
      const claudeRes = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": config.anthropicApiKey,
          "anthropic-version": "2023-06-01",
        },
        body: JSON.stringify({
          model: "claude-haiku-4-5-20251001",
          max_tokens: 600,
          system: systemPrompt,
          messages,
        }),
        signal: AbortSignal.timeout(15000),
      });
      if (claudeRes.ok) {
        const data = await claudeRes.json();
        const text = data?.content?.[0]?.text?.trim();
        if (text) return res.json({ response: text, provider: "claude" });
      }
    } catch { /* fall through */ }
  }

  // ── 2. Gemini Flash Lite ────────────────────────────────────────────────
  if (config.geminiApiKey) {
    try {
      const geminiRes = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key=${config.geminiApiKey}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            system_instruction: { parts: [{ text: systemPrompt }] },
            contents: messages.map((m) => ({
              role: m.role === "assistant" ? "model" : "user",
              parts: [{ text: m.content }],
            })),
            generationConfig: { maxOutputTokens: 600, temperature: 0.3 },
          }),
          signal: AbortSignal.timeout(15000),
        }
      );
      if (geminiRes.ok) {
        const data = await geminiRes.json();
        const text = data?.candidates?.[0]?.content?.parts?.[0]?.text?.trim();
        if (text) return res.json({ response: text, provider: "gemini" });
      }
    } catch { /* fall through */ }
  }

  // ── 3. Ollama local ─────────────────────────────────────────────────────
  const ollamaModels = ["qwen3:4b", "tinyllama:latest"];
  for (const model of ollamaModels) {
    try {
      const prompt = `${systemPrompt}\n\nUsuario: ${userMessage}`;
      const ollamaResp = await callOllama<{ response?: string }>("/api/generate", {
        model,
        prompt: `/no_think\n${prompt}`,
        stream: false,
        options: { num_predict: 500, temperature: 0.3 },
      });
      const text = ollamaResp?.response?.trim();
      if (text) return res.json({ response: text, provider: "ollama" });
    } catch { /* try next model */ }
  }

  // ── Fallback final ──────────────────────────────────────────────────────
  return res.json({
    response: "Lo siento, ningún proveedor de IA está disponible en este momento.",
    provider: "none",
  });
}));
```

---

## Variables de entorno necesarias

```env
ANTHROPIC_API_KEY=sk-ant-...      # Opcional — habilita Claude
GEMINI_API_KEY=AIza...            # Opcional — habilita Gemini
OLLAMA_HOST=http://localhost:11434 # Siempre disponible si Ollama corre
OLLAMA_TIMEOUT_MS=180000
```

---

## Modelos Ollama recomendados

| Modelo | Tamaño | Rol |
|--------|--------|-----|
| `qwen3:4b` | 2.5 GB | Principal — mejor calidad |
| `tinyllama:latest` | 637 MB | Fallback mínimo, muy rápido |
| `gemma4-fast:latest` | 9.6 GB | Alta calidad si disponible |

Instalar: `ollama pull qwen3:4b && ollama pull tinyllama`

---

## Cliente Ollama con timeout (`src/server/ollama.ts`)

```typescript
export async function callOllama<T>(endpoint: string, payload: unknown): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), config.ollamaTimeoutMs);
  try {
    const response = await fetch(`${config.ollamaHost}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`Ollama ${response.status}: ${await response.text()}`);
    return response.json() as Promise<T>;
  } finally {
    clearTimeout(timeout);
  }
}
```

**BUG CONOCIDO:** El endpoint debe incluir `/api/` — llamar `callOllama("/api/generate", ...)` NO `callOllama("generate", ...)`. Sin el prefijo, la URL queda `http://localhost:11434generate` y falla silenciosamente.

---

## System prompt dinámico (patrón)

```typescript
function buildSystemPrompt(session: SessionContext): string {
  return [
    "Eres el Asistente de [NOMBRE_APP]...",
    session.rules.length ? `REGLAS ACTIVAS:\n${session.rules.join('\n')}` : "",
    session.legalContext ? `MARCO JURÍDICO:\n${session.legalContext}` : "",
    session.currentQuery ? `CONTEXTO SESIÓN: búsqueda: ${session.currentQuery}` : "",
    session.openExpedient ? `EXPEDIENTE ABIERTO:\n${session.openExpedient}` : "",
    "Responde siempre en español. Sé preciso y orientado a la acción.",
  ].filter(Boolean).join("\n\n");
}
```

---

## Frontend: indicador de proveedor

```tsx
const PROVIDER_LABELS = {
  claude: { label: "Claude", color: "#d97706" },
  gemini: { label: "Gemini", color: "#1d4ed8" },
  ollama: { label: "Ollama Local", color: "#16a34a" },
  none:   { label: "Sin proveedor", color: "#dc2626" },
};

// En el componente de chat
<span style={{ color: PROVIDER_LABELS[provider].color }}>
  ● {PROVIDER_LABELS[provider].label}
</span>
```

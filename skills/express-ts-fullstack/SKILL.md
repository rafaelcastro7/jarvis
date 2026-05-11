---
name: express-ts-fullstack
description: Patrón full-stack Express+TypeScript+Vite con servidor dual (dev con HMR / prod con static), PostgreSQL con fallback in-memory, asyncHandler, HttpError, code splitting por vendor, y scripts de utilidad. Probado en Node 24.
tools: Read, Edit, Write, Bash
---

# Express + TypeScript + Vite — Full-Stack Pattern

## Estructura de archivos

```
proyecto/
├── server.ts               # Entry point (tsx server.ts)
├── src/
│   ├── main.tsx            # React entry
│   ├── App.tsx             # Root component
│   └── server/
│       ├── app.ts          # Express app + rutas
│       ├── config.ts       # Variables de entorno tipadas
│       ├── database.ts     # Pool PostgreSQL + fallback in-memory
│       ├── http.ts         # HttpError + asyncHandler + validators
│       └── ollama.ts       # Proxy cliente a Ollama
├── vite.config.ts
├── tsconfig.json
├── package.json
├── .env
└── .env.example
```

---

## `server.ts` — Entry point

```typescript
import { createServer } from "http";
import { createApp } from "./src/server/app";
import { config } from "./src/server/config";

async function main() {
  const app = await createApp();
  const server = createServer(app);
  server.listen(config.port, "0.0.0.0", () => {
    console.log(`Server running on http://0.0.0.0:${config.port}`);
  });
}

main().catch((err) => { console.error(err); process.exit(1); });
```

---

## `src/server/config.ts` — Variables tipadas

```typescript
function readInt(key: string, fallback: number): number {
  const v = parseInt(process.env[key] || "");
  return isNaN(v) ? fallback : v;
}

export const config = {
  nodeEnv:         process.env.NODE_ENV || "development",
  port:            readInt("PORT", 3000),
  jsonLimit:       process.env.JSON_LIMIT || "10mb",
  ollamaHost:      process.env.OLLAMA_HOST || "http://localhost:11434",
  ollamaTimeoutMs: readInt("OLLAMA_TIMEOUT_MS", 60000),
  anthropicApiKey: process.env.ANTHROPIC_API_KEY || "",
  geminiApiKey:    process.env.GEMINI_API_KEY || "",
  database: {
    host:     process.env.DB_HOST || "localhost",
    user:     process.env.DB_USER || "postgres",
    password: process.env.DB_PASSWORD || "postgres",
    name:     process.env.DB_NAME || "myapp",
    port:     readInt("DB_PORT", 5432),
  },
};

export const isProduction = config.nodeEnv === "production";
```

---

## `src/server/http.ts` — Error handling

```typescript
export class HttpError extends Error {
  constructor(public statusCode: number, message: string, public details?: unknown) {
    super(message);
  }
}

type AsyncHandler = (
  req: import("express").Request,
  res: import("express").Response,
  next: import("express").NextFunction
) => Promise<void>;

export function asyncHandler(fn: AsyncHandler) {
  return (
    req: import("express").Request,
    res: import("express").Response,
    next: import("express").NextFunction
  ) => {
    fn(req, res, next).catch(next);
  };
}

export function handleApiError(
  error: unknown,
  res: import("express").Response
) {
  if (error instanceof HttpError) {
    return res.status(error.statusCode).json({
      error: error.message,
      details: error.details,
    });
  }
  console.error("[Server Error]", error);
  return res.status(500).json({ error: "Internal server error" });
}

// Validators
export function requireString(value: unknown, field: string): string {
  if (typeof value !== "string" || !value.trim()) {
    throw new HttpError(400, `Missing or invalid field: ${field}`);
  }
  return value.trim();
}
```

---

## `src/server/database.ts` — Pool con fallback in-memory

```typescript
import { Pool } from "pg";
import { config } from "./config";

const pool = new Pool({
  host: config.database.host,
  user: config.database.user,
  password: config.database.password,
  database: config.database.name,
  port: config.database.port,
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

let databaseMode: "postgres" | "memory" = "postgres";
const memoryStore = new Map<string, { data: string; timestamp: number }>();

export async function initDatabase() {
  try {
    await pool.query("SELECT 1");
    await pool.query(`
      CREATE TABLE IF NOT EXISTS analysis_cache (
        groupkey TEXT PRIMARY KEY,
        data TEXT NOT NULL,
        timestamp BIGINT NOT NULL
      )
    `);
    console.log("[DB] PostgreSQL connected");
  } catch (err) {
    console.warn("[DB] PostgreSQL unavailable, using in-memory fallback");
    databaseMode = "memory";
  }
}

export async function query<T = Record<string, unknown>>(
  text: string,
  params: unknown[] = []
): Promise<{ rows: T[]; rowCount: number }> {
  if (databaseMode === "memory") {
    return queryInMemory<T>(text, params);
  }
  try {
    const result = await pool.query(text, params);
    return { rows: result.rows as T[], rowCount: result.rowCount ?? 0 };
  } catch (err) {
    databaseMode = "memory";
    return queryInMemory<T>(text, params);
  }
}
```

---

## `src/server/app.ts` — Servidor dual dev/prod

```typescript
import express from "express";
import path from "path";
import { config, isProduction } from "./config";
import { initDatabase } from "./database";
import { handleApiError } from "./http";

export async function createApp() {
  await initDatabase();

  const app = express();
  app.use(express.json({ limit: config.jsonLimit }));
  app.use(express.urlencoded({ extended: true }));

  // ── API routes ────────────────────────────────────────────────────────
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", ollamaHost: config.ollamaHost });
  });

  // ... más rutas ...

  // ── Error handler ─────────────────────────────────────────────────────
  app.use((err: unknown, req: express.Request, res: express.Response, _next: express.NextFunction) => {
    handleApiError(err, res);
  });

  // ── Static / Dev server ───────────────────────────────────────────────
  if (!isProduction) {
    const { createServer: createViteServer } = await import("vite");
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  return app;
}
```

---

## `vite.config.ts` — Code splitting óptimo

```typescript
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, ".") } },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules/react")) return "react-vendor";
          if (id.includes("framer-motion") || id.includes("/motion/")) return "motion-vendor";
          if (id.includes("recharts")) return "charts-vendor";
          if (id.includes("html2canvas")) return "html2canvas-vendor";
          if (id.includes("jspdf")) return "jspdf-vendor";
          if (id.includes("@huggingface")) return "transformers-vendor";
        },
      },
    },
  },
});
```

Tamaños típicos tras splitting:
- `react-vendor`: ~200 KB gzip
- `motion-vendor`: ~42 KB gzip
- `charts-vendor`: ~110 KB gzip
- `index`: ~27 KB gzip (código de app)

---

## `package.json` — Scripts completos

```json
{
  "scripts": {
    "dev":     "tsx server.ts",
    "start":   "cross-env NODE_ENV=production tsx server.ts",
    "build":   "vite build && node -e \"require('fs').copyFileSync('script.py','dist/script.py')\"",
    "restart": "powershell -ExecutionPolicy Bypass -File restart-server.ps1",
    "lint":    "tsc --noEmit",
    "clean":   "node -e \"require('fs').rmSync('dist', { recursive: true, force: true })\""
  }
}
```

---

## `.env.example`

```env
PORT=3055

DB_HOST=localhost
DB_PORT=5433
DB_NAME=myapp
DB_USER=myuser
DB_PASSWORD=changeme

OLLAMA_HOST=http://localhost:11434
OLLAMA_TIMEOUT_MS=180000

JSON_LIMIT=50mb

ANTHROPIC_API_KEY=
GEMINI_API_KEY=
```

---

## Checklist de deployment

1. `npm run lint` — 0 errores TS
2. `npm run build` — bundle generado en `dist/`
3. Verificar cloudflared activo (ver `/tunnel-manager`)
4. `npm run restart` — restart seguro
5. `curl http://localhost:PORT/api/health` → `{"status":"ok"}`
6. Probar URL pública

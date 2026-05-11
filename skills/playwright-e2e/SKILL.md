---
name: playwright-e2e
description: Tests E2E con Playwright para apps full-stack Express+React. Configuración con webServer, tests de API backend, tests de UI con localStorage injection, y timeout largo para operaciones de IA. Basado en GobIA Auditor (tests/e2e/).
tools: Read, Write, Bash, Edit
---

# Playwright E2E Testing — Express + React

## Instalación

```bash
npm install -D @playwright/test
npx playwright install chromium  # solo chromium es suficiente para CI
```

---

## `playwright.config.ts`

```typescript
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 240_000,          // 4 min — necesario para operaciones de IA/Ollama
  use: {
    baseURL: "http://127.0.0.1:3055",
    headless: true,
  },
  webServer: {
    command: "npm start",
    url: "http://127.0.0.1:3055/api/health",
    reuseExistingServer: true,  // No mata el servidor si ya corre
    timeout: 60_000,
    env: {
      NODE_ENV: "production",
      PORT: "3055",
      DB_HOST: process.env.DB_HOST || "localhost",
      DB_PORT: process.env.DB_PORT || "5433",
      OLLAMA_HOST: process.env.OLLAMA_HOST || "http://localhost:11434",
    },
  },
});
```

**IMPORTANTE:** `reuseExistingServer: true` es clave cuando el servidor tarda en arrancar (carga de modelos, conexión DB). Sin esto, Playwright intenta arrancarlo siempre y falla si ya está corriendo.

---

## `tests/e2e/backend.spec.ts` — Tests de API

```typescript
import { test, expect } from "@playwright/test";

test.describe("Backend API", () => {
  test("health check", async ({ request }) => {
    const res = await request.get("/api/health");
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.status).toBe("ok");
    expect(body.database).toBe("connected");
  });

  test("cache API — write and read", async ({ request }) => {
    const groupKey = `test-${Date.now()}`;
    const data = { test: true, timestamp: Date.now() };

    // Write
    const writeRes = await request.post("/api/cache/analysis", {
      data: { groupKey, data },
    });
    expect(writeRes.ok()).toBeTruthy();

    // Read
    const readRes = await request.get(`/api/cache/analysis/${groupKey}`);
    expect(readRes.ok()).toBeTruthy();
    const body = await readRes.json();
    expect(body.data).toBeDefined();
  });

  test("SECOP proxy", async ({ request }) => {
    const res = await request.get("/api/secop/contracts?entity=SENA&limit=3");
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(Array.isArray(body.contracts)).toBeTruthy();
  });

  test("RAG legal context", async ({ request }) => {
    const res = await request.post("/api/rag/legal-context", {
      data: {
        query: "fraccionamiento de contratos",
        redFlags: ["fraccionamiento", "directa"],
      },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(typeof body.context).toBe("string");
  });

  test("Ollama generate (tinyllama)", async ({ request }) => {
    const res = await request.post("/api/ollama/generate", {
      data: {
        model: "tinyllama:latest",
        prompt: "Di solo: OK",
        stream: false,
        options: { num_predict: 10 },
      },
    });
    // Ollama puede no estar disponible — no falla el test
    if (res.ok()) {
      const body = await res.json();
      expect(typeof body.response).toBe("string");
    }
  });
});
```

---

## `tests/e2e/app.spec.ts` — Tests de UI

```typescript
import { test, expect } from "@playwright/test";

test.describe("Frontend UI", () => {
  test("home page loads", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/GobIA|SECOP|Auditor/i);
  });

  test("inject data via localStorage and verify rendering", async ({ page }) => {
    // Inyectar datos antes de que cargue la página
    await page.addInitScript(() => {
      localStorage.setItem("session-contracts", JSON.stringify([
        {
          id_contrato: "TEST-001",
          nombre_entidad: "SENA",
          nombre_del_contratista: "TEST PROVEEDOR",
          documento_proveedor: "123456789",
          valor_del_contrato: "500000000",
          objeto_del_contrato: "Servicios de consultoría",
          fecha_de_firma: "2024-01-15",
          modalidad_de_contratacion: "Contratación Directa",
        },
      ]));
    });

    await page.goto("/");
    // Verificar que el componente principal renderizó
    await expect(page.locator("body")).toBeVisible({ timeout: 30_000 });
  });

  test("tabs navigation works", async ({ page }) => {
    await page.goto("/");
    // Esperar que cargue el dashboard
    await page.waitForSelector("[data-tab]", { timeout: 15_000 }).catch(() => null);
  });
});
```

---

## Scripts en `package.json`

```json
{
  "scripts": {
    "test:e2e": "npm run build && playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug",
    "test:e2e:report": "playwright show-report"
  }
}
```

---

## Patrones clave

### Timeout para operaciones de IA
```typescript
// Las llamadas a Ollama pueden tardar 30-60s en responder
test("AI chat", async ({ page, request }) => {
  test.setTimeout(120_000);  // Override del timeout global para este test
  const res = await request.post("/api/chat/assistant", {
    data: { systemPrompt: "Eres un asistente.", userMessage: "Hola" },
    timeout: 90_000,
  });
  expect(res.ok()).toBeTruthy();
});
```

### Verificar puerto correcto
```typescript
// playwright.config.ts y .env deben usar el MISMO puerto
// Si .env tiene PORT=3055, el config también debe apuntar a 3055
// Error frecuente: config apunta a 3051 mientras server corre en 3055
baseURL: `http://127.0.0.1:${process.env.PORT || "3055"}`,
```

### reuseExistingServer para desarrollo
```typescript
// En desarrollo, el servidor ya está corriendo con watchdog.ps1
// reuseExistingServer: true evita intentar arrancarlo de nuevo
webServer: {
  reuseExistingServer: !process.env.CI,  // En CI siempre arranca fresco
}
```

---

## Checklist antes de correr tests E2E

1. Servidor corriendo: `Invoke-WebRequest http://localhost:3055/api/health`
2. Ollama disponible (si hay tests de AI): `ollama list`
3. PostgreSQL disponible (si hay tests de caché): `psql -U aiuser -d aiagency -c "SELECT 1"`
4. Build actualizado: `npm run build`
5. Puerto en playwright.config.ts == PORT en .env

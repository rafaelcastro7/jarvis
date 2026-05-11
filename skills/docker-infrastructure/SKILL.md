---
name: docker-infrastructure
description: Docker + Docker Compose para stack Node.js + PostgreSQL + Ollama. Multi-stage build, red compartida, variables de entorno por servicio. Basado en GobIA Auditor. Incluye setup local sin Docker para desarrollo.
tools: Read, Write, Bash, PowerShell
---

# Docker Infrastructure — Node + PostgreSQL + Ollama

## Dockerfile (multi-stage)

```dockerfile
# ── Stage 1: deps ────────────────────────────────────────────────────────────
FROM node:24-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# ── Stage 2: build ───────────────────────────────────────────────────────────
FROM deps AS build
COPY . .
RUN npm run build
RUN npm prune --production

# ── Stage 3: runtime ─────────────────────────────────────────────────────────
FROM node:24-alpine AS runtime
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/src ./src
COPY --from=build /app/server.ts ./server.ts
COPY --from=build /app/package.json ./package.json

EXPOSE 3055
CMD ["npm", "start"]
```

**Por qué 3 stages:**
1. `deps` — instala dependencias una vez, reutilizable si package.json no cambia
2. `build` — compila y poda devDependencies
3. `runtime` — imagen mínima con solo lo necesario (~200MB vs ~1GB)

---

## docker-compose.yml

```yaml
version: "3.9"

networks:
  ai-net:
    external: true  # Crear con: docker network create ai-net

services:
  app:
    build: .
    ports:
      - "3055:3055"
    environment:
      NODE_ENV: production
      PORT: 3055
      DB_HOST: postgres
      DB_PORT: 5432
      DB_USER: aiuser
      DB_PASSWORD: changeme
      DB_NAME: aiagency
      OLLAMA_HOST: http://host.docker.internal:11434  # Ollama en host local
      OLLAMA_TIMEOUT_MS: 180000
      JSON_LIMIT: 50mb
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      GEMINI_API_KEY: ${GEMINI_API_KEY:-}
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - ai-net
    restart: unless-stopped

  postgres:
    image: pgvector/pgvector:pg16  # PostgreSQL 16 con extensión pgvector
    environment:
      POSTGRES_USER: aiuser
      POSTGRES_PASSWORD: changeme
      POSTGRES_DB: aiagency
    ports:
      - "5433:5432"  # Puerto 5433 externo para no colisionar con Postgres local
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - ai-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aiuser -d aiagency"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
```

**NOTA sobre Ollama:** Ollama corre en el HOST (no en contenedor) porque necesita acceso directo a GPU. El contenedor lo accede via `host.docker.internal`.

---

## Setup inicial

```bash
# 1. Crear red compartida (una sola vez)
docker network create ai-net

# 2. Copiar y configurar env
cp .env.example .env
# Editar .env con tus valores

# 3. Build y arrancar
docker compose up -d --build

# 4. Verificar
docker compose ps
docker compose logs app --tail=20
```

---

## Setup local SIN Docker (Windows — desarrollo)

```powershell
# PostgreSQL local (Docker solo para DB)
docker run -d --name postgres-thegu `
  -e POSTGRES_USER=aiuser `
  -e POSTGRES_PASSWORD=changeme `
  -e POSTGRES_DB=aiagency `
  -p 5433:5432 `
  pgvector/pgvector:pg16

# Ollama (instalado nativamente para GPU)
# Descargar desde https://ollama.com
ollama pull nomic-embed-text
ollama pull qwen3:4b
ollama pull tinyllama

# App en modo desarrollo
npm run dev
```

---

## Variables de entorno por entorno

| Variable | Dev local | Docker Compose | Producción |
|----------|-----------|----------------|------------|
| `DB_HOST` | localhost | postgres (service name) | IP del servidor |
| `DB_PORT` | 5433 | 5432 (interno) | 5432 |
| `OLLAMA_HOST` | http://localhost:11434 | http://host.docker.internal:11434 | http://localhost:11434 |
| `PORT` | 3055 | 3055 | 3055 |

---

## Comandos útiles

```bash
# Ver logs en tiempo real
docker compose logs -f app

# Reiniciar solo la app (sin tocar DB)
docker compose restart app

# Entrar al contenedor
docker compose exec app sh

# Ver estado de DB
docker compose exec postgres psql -U aiuser -d aiagency -c "\dt"

# Backup de DB
docker compose exec postgres pg_dump -U aiuser aiagency > backup.sql

# Limpiar todo (DESTRUCTIVO)
docker compose down -v  # elimina volúmenes también
```

---

## Healthcheck personalizado para app

```yaml
# Agregar al servicio app en docker-compose.yml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:3055/api/health || exit 1"]
  interval: 15s
  timeout: 5s
  retries: 3
  start_period: 30s  # Dar tiempo al servidor para arrancar
```

---

## .dockerignore

```
node_modules/
dist/
.env
*.log
.git/
RETO/
*.csv
*.zip
```

# setup.ps1 — Instala Jarvis en Windows desde cero
# Ejecutar como Admin: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

param([switch]$SkipOllama, [switch]$SkipDocker)

Write-Host "=== JARVIS SETUP ===" -ForegroundColor Cyan
Write-Host "Instalando dependencias..."

$JARVIS_DIR = $PSScriptRoot

# --- 1. Verificar/instalar Python ---
try {
    $pyVer = python --version 2>&1
    Write-Host "[OK] Python: $pyVer"
} catch {
    Write-Host "[!] Python no encontrado. Instalando via winget..."
    winget install Python.Python.3.12 -e --silent
    $env:PATH += ";$env:LOCALAPPDATA\Programs\Python\Python312"
}

# --- 2. Dependencias Python ---
Write-Host "`nInstalando dependencias Python..."
pip install playwright requests aiohttp anthropic ollama openai --quiet
python -m playwright install chromium
Write-Host "[OK] Playwright instalado"

# --- 3. Ollama ---
if (-not $SkipOllama) {
    $ollamaRunning = $false
    try {
        $resp = Invoke-WebRequest "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 3
        $ollamaRunning = $true
        Write-Host "[OK] Ollama ya está corriendo"
    } catch {}

    if (-not $ollamaRunning) {
        $ollamaPath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
        if (-not (Test-Path $ollamaPath)) {
            Write-Host "[!] Ollama no encontrado. Descargando..."
            $ollamaInstaller = "$env:TEMP\OllamaSetup.exe"
            Invoke-WebRequest "https://ollama.com/download/OllamaSetup.exe" -OutFile $ollamaInstaller
            Start-Process $ollamaInstaller -Wait -ArgumentList "/S"
        }
        Write-Host "Iniciando Ollama..."
        Start-Process "$ollamaPath" -ArgumentList "serve" -WindowStyle Minimized
        Start-Sleep 5
    }

    Write-Host "`nDescargando modelos Ollama (puede tardar 20-40 min en primera instalación)..."
    $models = @("nomic-embed-text", "qwen3:4b", "qwen2.5-coder:7b")
    foreach ($model in $models) {
        Write-Host "  Pulling $model..."
        ollama pull $model
    }
    Write-Host "[OK] Modelos Ollama instalados"
}

# --- 4. Docker + OpenWebUI ---
if (-not $SkipDocker) {
    $dockerRunning = $false
    try {
        docker ps 2>&1 | Out-Null
        $dockerRunning = $true
    } catch {}

    if ($dockerRunning) {
        Write-Host "`nIniciando OpenWebUI (ChatGPT local)..."
        docker compose -f "$JARVIS_DIR\docker-compose.yml" up -d
        Write-Host "[OK] OpenWebUI en http://localhost:3000"
    } else {
        Write-Host "[!] Docker no encontrado — instala Docker Desktop desde https://docker.com"
        Write-Host "    Luego ejecuta: docker compose up -d"
    }
}

# --- 5. Instalar Aider (Claude Code local) ---
Write-Host "`nInstalando Aider (coding assistant local)..."
pip install aider-chat --quiet
Write-Host "[OK] Aider instalado — uso: aider --model ollama/qwen2.5-coder:7b"

# --- 6. Instalar skills de Claude Code ---
Write-Host "`nInstalando Claude Code skills..."
$claudeSkillsDir = "$env:USERPROFILE\.claude\skills"
New-Item -ItemType Directory -Path $claudeSkillsDir -Force | Out-Null

$srcSkills = "$JARVIS_DIR\skills"
if (Test-Path $srcSkills) {
    Copy-Item -Path "$srcSkills\*" -Destination $claudeSkillsDir -Recurse -Force
    $count = (Get-ChildItem $claudeSkillsDir -Directory).Count
    Write-Host "[OK] $count skills instalados en $claudeSkillsDir"
}

# --- 7. Verificar instalación ---
Write-Host "`n=== VERIFICACION ===" -ForegroundColor Green
Write-Host "Python:   $(python --version 2>&1)"
Write-Host "Pip:      $(pip --version 2>&1 | Select-String '\d+\.\d+')"
try { Write-Host "Ollama:   $(ollama list 2>&1 | head -1)" } catch {}
try { Write-Host "OpenWebUI: http://localhost:3000" } catch {}
Write-Host "Skills:   $((Get-ChildItem $claudeSkillsDir -Directory -ErrorAction SilentlyContinue).Count) skills"

Write-Host @"

=== JARVIS LISTO ===
Chat UI:    http://localhost:3000   (OpenWebUI — requiere Docker)
Ollama API: http://localhost:11434
Aider:      aider --model ollama/qwen2.5-coder:7b --no-auto-commits
RAG:        python src/rag/ingest.py  (indexar knowledge/)

Skills Claude Code activos:
  /anthropic-architect  — Diseño de sistemas con Claude
  /site-cloner          — Scraping de plataformas LMS
  /ollama-local         — Gestión de modelos Ollama
  /hls-video-downloader — Descarga de videos HLS
  /react-course-player  — Player LMS React
"@

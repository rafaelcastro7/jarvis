#!/bin/bash
# setup.sh — Instala Jarvis en Linux/Mac desde cero
set -e

JARVIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== JARVIS SETUP (Linux/Mac) ==="

# --- 1. Python ---
if ! command -v python3 &>/dev/null; then
    echo "[!] Instalando Python..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install python3
    else
        sudo apt-get update && sudo apt-get install -y python3 python3-pip
    fi
fi
echo "[OK] Python: $(python3 --version)"

# --- 2. Dependencias Python ---
echo "Instalando dependencias Python..."
pip3 install playwright requests aiohttp anthropic ollama openai aider-chat -q
python3 -m playwright install chromium
echo "[OK] Playwright + Aider instalados"

# --- 3. Ollama ---
if ! command -v ollama &>/dev/null; then
    echo "Instalando Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

if ! pgrep -x "ollama" > /dev/null; then
    ollama serve &>/dev/null &
    sleep 5
fi
echo "[OK] Ollama corriendo"

echo "Descargando modelos (puede tardar)..."
ollama pull nomic-embed-text
ollama pull qwen3:4b
ollama pull qwen2.5-coder:7b
echo "[OK] Modelos instalados"

# --- 4. Docker + OpenWebUI ---
if command -v docker &>/dev/null; then
    docker compose -f "$JARVIS_DIR/docker-compose.yml" up -d
    echo "[OK] OpenWebUI en http://localhost:3000"
else
    echo "[!] Docker no instalado — instala desde https://docker.com"
fi

# --- 5. Skills Claude Code ---
CLAUDE_SKILLS="$HOME/.claude/skills"
mkdir -p "$CLAUDE_SKILLS"
cp -r "$JARVIS_DIR/skills/"* "$CLAUDE_SKILLS/"
echo "[OK] $(ls "$CLAUDE_SKILLS" | wc -l) skills instalados"

echo ""
echo "=== JARVIS LISTO ==="
echo "Chat UI:    http://localhost:3000"
echo "Ollama API: http://localhost:11434"
echo "Aider:      aider --model ollama/qwen2.5-coder:7b --no-auto-commits"
echo "RAG:        python3 src/rag/ingest.py"

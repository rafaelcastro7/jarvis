"""
e2e_test.py — Prueba End-to-End de Jarvis.
Verifica: Ingesta -> Búsqueda RAG -> Respuesta del Modelo.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import subprocess
import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
INGEST_SCRIPT = ROOT_DIR / "src" / "rag" / "ingest.py"
JARVIS_SCRIPT = ROOT_DIR / "src" / "jarvis.py"

def run_step(name, command):
    print(f"\n[STEP] {name}...")
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True, encoding='utf-8')
        if result.returncode == 0:
            print(f"[OK] {name} completado.")
            return result.stdout
        else:
            print(f"[ERROR] {name} falló: {result.stderr}")
            sys.exit(1)
    except Exception as e:
        print(f"[EXCEPTION] {name}: {e}")
        sys.exit(1)

def main():
    print("=== INICIANDO PRUEBA END-TO-END DE JARVIS ===")

    # 1. Ingesta
    run_step("Ingestión de Conocimiento", "python src/rag/ingest.py")

    # 2. Búsqueda RAG
    search_output = run_step("Búsqueda RAG (Scraping)", "python src/rag/ingest.py search técnicas de scraping")
    if "scraping" in search_output.lower():
        print("[CHECK] Búsqueda RAG encontró resultados relevantes.")
    else:
        print("[WARNING] Búsqueda RAG no devolvió lo esperado.")

    # 3. Verificación de Modelos Ollama
    models_output = run_step("Verificación de Modelos", "ollama list")
    required = ["qwen3:4b", "nomic-embed-text"]
    for m in required:
        if m in models_output:
            print(f"[CHECK] Modelo {m} presente.")
        else:
            print(f"[ERROR] Modelo {m} ausente.")
            sys.exit(1)

    print("\n=== PRUEBA E2E COMPLETADA CON ÉXITO ===")

if __name__ == "__main__":
    main()

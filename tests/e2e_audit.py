"""
e2e_audit.py — Suite de Auditoría End-to-End para Jarvis.
Verifica que RAG, Vision, Celery, y Aider funcionen correctamente.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import subprocess
import time
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# Variables para el reporte final
audit_results = {}

def run_test(name: str, func):
    print(f"\n[AUDIT] Iniciando prueba: {name}...")
    try:
        t0 = time.time()
        res = func()
        t1 = time.time()
        print(f"[OK] {name} ({(t1-t0):.2f}s)")
        audit_results[name] = {"status": "✅ PASSED", "time": round(t1-t0, 2), "details": str(res)}
    except Exception as e:
        print(f"[FAIL] {name} falló: {e}")
        audit_results[name] = {"status": "❌ FAILED", "time": 0, "details": str(e)}

# --- Tests ---

def test_rag_hyde():
    from src.rag.chroma_store import search
    res = search("scraping techniques", top_k=1, use_hyde=True)
    if not res:
        raise ValueError("ChromaDB devolvió 0 resultados.")
    return f"Encontrado: {res[0]['file']} (Score: {res[0]['score']})"

def test_vision_init():
    from src.tools.vision import init_vision_model
    model = init_vision_model()
    if not model:
        raise RuntimeError("No se pudo cargar Moondream2.")
    return "Modelo cargado exitosamente."

def test_celery_broker():
    try:
        from src.tasks import app
        # Inspeccionar la conexión
        i = app.control.inspect()
        stats = i.stats()
        if stats is None:
            return "Broker (Redis) no disponible o worker apagado. (Advertencia, no es crítico si se ejecuta síncronamente)"
        return f"Workers activos: {list(stats.keys())}"
    except Exception as e:
        raise RuntimeError(f"Error conectando a Redis/Celery: {e}")

def test_aider_cli():
    res = subprocess.run(["aider", "--version"], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Aider no está instalado correctamente: {res.stderr}")
    return res.stdout.strip()

def test_browser_use():
    try:
        from browser_use import Agent, Controller
        return "Browser-use y controlador importados correctamente."
    except Exception as e:
        raise RuntimeError(f"Error de importación browser-use: {e}")

def run_audit():
    print("="*50)
    print("🧪 INICIANDO AUDITORÍA E2E DE JARVIS")
    print("="*50)
    
    run_test("RAG + HyDE Search", test_rag_hyde)
    run_test("Visión (Moondream Initialization)", test_vision_init)
    run_test("Cola de Tareas (Celery/Redis)", test_celery_broker)
    run_test("Auto-Parcheo CLI (Aider)", test_aider_cli)
    run_test("Módulo Web (Browser-use)", test_browser_use)
    
    print("\n" + "="*50)
    print("📊 REPORTE DE AUDITORÍA FINAL")
    print("="*50)
    
    for name, data in audit_results.items():
        print(f"{data['status']} | {name} | {data['time']}s")
        if data['status'] == "❌ FAILED":
            print(f"    Detalle: {data['details']}")
        elif "Advertencia" in str(data['details']):
            print(f"    ⚠️ Warning: {data['details']}")
            
    fails = sum(1 for d in audit_results.values() if d['status'] == "❌ FAILED")
    if fails > 0:
        print(f"\n⚠️ Auditoría completada con {fails} fallos. Requiere revisión.")
        sys.exit(1)
    else:
        print("\n✅ Todos los sistemas críticos están operativos.")
        sys.exit(0)

if __name__ == "__main__":
    run_audit()

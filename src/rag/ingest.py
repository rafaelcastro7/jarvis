"""
ingest.py — Indexa todos los documentos de knowledge/ en una base vectorial local.
Usa nomic-embed-text (Ollama) + JSON file store (sin base de datos externa).
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import json
import re
from pathlib import Path

try:
    import ollama
except ImportError:
    print("Instala: pip install ollama"); sys.exit(1)

JARVIS_DIR = Path(__file__).parent.parent.parent
KNOWLEDGE_DIR = JARVIS_DIR / "knowledge"
INDEX_FILE = JARVIS_DIR / "src" / "rag" / "index.json"
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE = 800


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks, current = [], ""
    for para in paragraphs:
        if len(current) + len(para) > size and current:
            chunks.append(current.strip())
            current = para
        else:
            current = (current + "\n\n" + para).strip()
    if current:
        chunks.append(current)
    return chunks


def embed(text: str) -> list[float]:
    resp = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return resp["embedding"]


def cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x**2 for x in a) ** 0.5
    mag_b = sum(x**2 for x in b) ** 0.5
    return dot / (mag_a * mag_b + 1e-9)


def ingest():
    index = []
    md_files = list(KNOWLEDGE_DIR.rglob("*.md"))
    print(f"Indexando {len(md_files)} archivos de {KNOWLEDGE_DIR}...")

    for md_file in md_files:
        text = md_file.read_text(encoding='utf-8', errors='ignore')
        chunks = chunk_text(text)
        rel_path = str(md_file.relative_to(JARVIS_DIR))

        for i, chunk in enumerate(chunks):
            try:
                vec = embed(chunk)
                index.append({
                    "file": rel_path,
                    "chunk": i,
                    "text": chunk[:500],
                    "embedding": vec,
                })
                print(f"  [{rel_path}] chunk {i+1}/{len(chunks)}")
            except Exception as e:
                print(f"  [ERROR] {rel_path} chunk {i}: {e}")

    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False), encoding='utf-8')
    print(f"\nIndexados {len(index)} chunks → {INDEX_FILE}")


def search(query: str, top_k: int = 5) -> list[dict]:
    if not INDEX_FILE.exists():
        print("Ejecuta primero: python src/rag/ingest.py")
        return []

    index = json.loads(INDEX_FILE.read_text(encoding='utf-8'))
    q_vec = embed(query)
    scored = [(cosine_sim(q_vec, item["embedding"]), item) for item in index]
    scored.sort(reverse=True, key=lambda x: x[0])
    return [{"score": round(s, 3), **item} for s, item in scored[:top_k]]


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        query = " ".join(sys.argv[2:]) or "agentic loop"
        results = search(query)
        for r in results:
            print(f"\n[{r['score']}] {r['file']} chunk {r['chunk']}")
            print(r['text'][:300])
    else:
        ingest()

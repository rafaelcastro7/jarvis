"""
ingest.py — Indexa todos los documentos de knowledge/ y skills/ en una base vectorial local.
Usa nomic-embed-text (Ollama) + JSON file store.
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
SKILLS_DIR = JARVIS_DIR / "skills"
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


def extract_text(file_path: Path) -> str:
    if file_path.suffix.lower() in [".md", ".txt"]:
        return file_path.read_text(encoding='utf-8', errors='ignore')
    elif file_path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        except Exception as e:
            print(f"  [ERROR] No se pudo leer PDF {file_path.name}: {e}")
            return ""
    return ""


def ingest():
    index = []
    extensions = ["*.md", "*.txt", "*.pdf"]
    files = []
    
    # Buscar en knowledge y skills
    for root in [KNOWLEDGE_DIR, SKILLS_DIR]:
        if not root.exists(): continue
        for ext in extensions:
            files.extend(list(root.rglob(ext)))
    
    print(f"Indexando {len(files)} archivos...")

    for f in files:
        text = extract_text(f)
        if not text:
            continue
            
        chunks = chunk_text(text)
        rel_path = str(f.relative_to(JARVIS_DIR))

        for i, chunk in enumerate(chunks):
            try:
                vec = embed(chunk)
                index.append({
                    "file": rel_path,
                    "chunk": i,
                    "text": chunk[:800],
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
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        query = " ".join(sys.argv[2:]) or "agentic loop"
        results = search(query)
        for r in results:
            print(f"\n[{r['score']}] {r['file']} chunk {r['chunk']}")
            print(r['text'][:300])
    else:
        ingest()

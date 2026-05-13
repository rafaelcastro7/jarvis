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
    from chroma_store import add_documents, reset_db
    
    # Limpiamos la base de datos anterior si vamos a re-indexar todo
    reset_db()
    
    extensions = ["*.md", "*.txt", "*.pdf"]
    files = []
    
    # Buscar en knowledge y skills
    for root in [KNOWLEDGE_DIR, SKILLS_DIR]:
        if not root.exists(): continue
        for ext in extensions:
            files.extend(list(root.rglob(ext)))
    
    print(f"Indexando {len(files)} archivos en ChromaDB...")

    texts_batch = []
    meta_batch = []

    for f in files:
        text = extract_text(f)
        if not text:
            continue
            
        chunks = chunk_text(text)
        rel_path = str(f.relative_to(JARVIS_DIR))

        for i, chunk in enumerate(chunks):
            texts_batch.append(chunk)
            meta_batch.append({"source": rel_path, "chunk_id": i})
            
            # Guardamos en lotes de 100 para no saturar memoria/Chroma
            if len(texts_batch) >= 100:
                add_documents(texts_batch, meta_batch)
                texts_batch = []
                meta_batch = []

    if texts_batch:
        add_documents(texts_batch, meta_batch)
        
    print(f"\n✅ Indexación completada con ChromaDB.")


def search(query: str, top_k: int = 5) -> list[dict]:
    from chroma_store import search as chroma_search
    return chroma_search(query, top_k=top_k)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        query = " ".join(sys.argv[2:]) or "agentic loop"
        results = search(query)
        for r in results:
            print(f"\n[Score: {r['score']}] {r['file']} chunk {r['chunk']}")
            print(r['text'][:300])
    else:
        ingest()


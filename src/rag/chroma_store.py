"""
chroma_store.py — Base de datos vectorial persistente para Jarvis usando ChromaDB y LangChain.
Reemplaza el sistema JSON anterior para permitir consultas mucho más rápidas y escalables.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document

JARVIS_DIR = Path(__file__).parent.parent.parent
CHROMA_DB_DIR = JARVIS_DIR / "src" / "rag" / "chroma_db"
EMBED_MODEL = "nomic-embed-text"

def get_embeddings():
    """Retorna la instancia de embeddings de Ollama."""
    # Usamos nomic-embed-text que ya descargamos localmente
    return OllamaEmbeddings(model=EMBED_MODEL, base_url="http://localhost:11434")

def get_vectorstore():
    """Obtiene o inicializa la base de datos ChromaDB."""
    CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
    embeddings = get_embeddings()
    return Chroma(
        collection_name="jarvis_knowledge",
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DB_DIR)
    )

def add_documents(texts: list[str], metadatas: list[dict]):
    """Añade documentos a la base vectorial de forma segura."""
    if not texts:
        return
        
    vectorstore = get_vectorstore()
    
    docs = []
    for text, meta in zip(texts, metadatas):
        docs.append(Document(page_content=text, metadata=meta))
    
    vectorstore.add_documents(docs)
    vectorstore.persist()
    print(f"✅ {len(docs)} fragmentos guardados en ChromaDB.")

def search(query: str, top_k: int = 3):
    """Realiza una búsqueda de similitud en ChromaDB."""
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search_with_score(query, k=top_k)
    
    formatted_results = []
    for doc, score in results:
        # En Chroma, la distancia (score) menor es mejor similitud a menudo, pero Langchain normaliza en algunos casos.
        formatted_results.append({
            "file": doc.metadata.get("source", "Desconocido"),
            "chunk": doc.metadata.get("chunk_id", 0),
            "text": doc.page_content,
            "score": round(score, 4)
        })
    return formatted_results

def reset_db():
    """Limpia toda la base de datos (útil para re-indexar desde cero)."""
    if CHROMA_DB_DIR.exists():
        import shutil
        shutil.rmtree(CHROMA_DB_DIR)
        print("🗑️ Base de datos ChromaDB eliminada.")

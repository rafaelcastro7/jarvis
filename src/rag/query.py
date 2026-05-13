"""
query.py — Script de prueba para el sistema RAG de Jarvis.
Permite buscar en la base de conocimiento local sin entrar al chat completo.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
from ingest import search

def main():
    if len(sys.argv) < 2:
        print("Uso: python query.py \"tu pregunta\"")
        return

    query = " ".join(sys.argv[1:])
    print(f"Buscando: {query}...")
    
    results = search(query, top_k=3)
    
    if not results:
        print("No se encontraron resultados relevantes.")
        return

    print("-" * 60)
    for i, r in enumerate(results):
        print(f"\n[{i+1}] Score: {r['score']} | Fuente: {r['file']}")
        print(f"Contenido: {r['text']}...")
        print("-" * 30)

if __name__ == "__main__":
    main()

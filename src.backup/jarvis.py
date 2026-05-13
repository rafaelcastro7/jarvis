"""
jarvis.py — CLI principal de Jarvis, el asistente local.
Usa Ollama como backend (no requiere Claude API key).
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import asyncio
import json
from pathlib import Path

try:
    import ollama
except ImportError:
    print("Instala: pip install ollama")
    sys.exit(1)

from rag.ingest import search

JARVIS_DIR = Path(__file__).parent.parent
KNOWLEDGE_DIR = JARVIS_DIR / "knowledge"

MODEL_CHAT = "qwen3:4b"
MODEL_CODE = "qwen2.5-coder:7b"
MODEL_EMBED = "nomic-embed-text"

SYSTEM_PROMPT = f"""Eres Jarvis, el asistente personal de Rafael Castro.

Contexto sobre Rafael:
- Full-stack dev: React+TS+Vite, Express+Node, Supabase, Odoo 18, Python
- Email: rafaelc@braintrainr.ai
- Stack local: Ollama ({MODEL_CHAT} chat, {MODEL_CODE} código, {MODEL_EMBED} embeddings)
- Certificado: Anthropic Academy (4 cursos completados 2026-05-11)
- Objetivo: eliminar suscripciones de IA usando stack 100% local

Proyectos activos:
- OdooFactory v2: E:\\Documents\\PROYECTOS\\ODOO\\odoofactory2\\
- GobIA Auditor: E:\\Documents\\PROYECTOS\\AgencIA\\thegu\\
- AgencIA / OpenClaw: E:\\Documents\\PROYECTOS\\AgencIA\\
- RutaVital IA: E:\\Documents\\PROYECTOS\\MINTIC\\

Responde en español. Sé directo y técnico. Sin emojis a menos que el usuario los pida."""


def chat(messages: list, model: str = MODEL_CHAT) -> str:
    response = ollama.chat(
        model=model,
        messages=messages,
        options={"temperature": 0.3, "num_predict": 1000},
    )
    return response.message.content


def main():
    print("Jarvis v1.1 — Asistente local con RAG")
    print(f"Modelo: {MODEL_CHAT} | Código: {MODEL_CODE}")
    print("Comandos: /code, /chat, /rag (on/off), /reset, /exit")
    print("-" * 60)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    mode = "chat"
    use_rag = True

    while True:
        try:
            rag_status = "RAG: ON" if use_rag else "RAG: OFF"
            user_input = input(f"\n[{mode} | {rag_status}] Tu: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nHasta luego.")
            break

        if not user_input:
            continue

        if user_input == "/exit":
            print("Hasta luego.")
            break
        elif user_input == "/reset":
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            print("[Historial limpiado]")
            continue
        elif user_input == "/code":
            mode = "code"
            print(f"[Modo código activado — modelo: {MODEL_CODE}]")
            continue
        elif user_input == "/chat":
            mode = "chat"
            print(f"[Modo chat activado — modelo: {MODEL_CHAT}]")
            continue
        elif user_input == "/rag":
            use_rag = not use_rag
            print(f"[RAG {'activado' if use_rag else 'desactivado'}]")
            continue

        current_messages = messages.copy()
        
        if use_rag:
            results = search(user_input, top_k=3)
            if results:
                context = "\n".join([f"De {r['file']}:\n{r['text']}" for r in results])
                rag_prompt = f"Usa el siguiente contexto para responder si es relevante:\n{context}"
                current_messages.append({"role": "system", "content": rag_prompt})

        current_messages.append({"role": "user", "content": user_input})
        messages.append({"role": "user", "content": user_input}) # Persistir en el historial real
        model = MODEL_CODE if mode == "code" else MODEL_CHAT

        try:
            response = chat(current_messages, model=model)
            messages.append({"role": "assistant", "content": response})
            print(f"\nJarvis: {response}")
        except Exception as e:
            print(f"[Error Ollama: {e}]")
            print("¿Está Ollama corriendo? Ejecuta: ollama serve")


if __name__ == "__main__":
    main()

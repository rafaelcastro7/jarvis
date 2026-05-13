"""
vision.py — Herramienta de Visión para Jarvis usando Moondream.
Permite a Jarvis entender imágenes locales.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import warnings
from PIL import Image

# Ignorar advertencias de HuggingFace/Transformers para salida más limpia
warnings.filterwarnings("ignore")

# Instancia global para no recargar el modelo en cada llamada
_moondream_model = None

def init_vision_model():
    """Inicializa y cachea el modelo Moondream (pequeño y rápido)."""
    global _moondream_model
    if _moondream_model is None:
        print("Cargando modelo de visión Moondream2 (solo la primera vez)...")
        import moondream as md
        # moondream pypi package es un wrapper pequeño. A veces se carga directo desde transformers
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            model_id = "vikhyatk/moondream2"
            revision = "2024-08-26"
            
            # Usar AutoModel en vez de un wrapper si moondream es solo un nombre de paquete
            model = AutoModelForCausalLM.from_pretrained(
                model_id, trust_remote_code=True, revision=revision
            )
            tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
            _moondream_model = {"model": model, "tokenizer": tokenizer}
            print("✅ Modelo de visión cargado.")
        except Exception as e:
            print(f"Error cargando Moondream: {e}")
            return None
    return _moondream_model


def analyze_image(image_path: str, prompt: str = "Describe this image in detail.") -> str:
    """
    Analiza una imagen local y responde al prompt usando Moondream.
    """
    vision_sys = init_vision_model()
    if not vision_sys:
        return "Error: No se pudo inicializar el modelo de visión."
    
    try:
        image = Image.open(image_path)
        # Convertir a RGB por seguridad (Moondream espera RGB)
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        model = vision_sys["model"]
        tokenizer = vision_sys["tokenizer"]
        
        # Generar descripción
        # La API de moondream en transformers expone `encode_image` y `answer_question`
        enc_image = model.encode_image(image)
        answer = model.answer_question(enc_image, prompt, tokenizer)
        return answer

    except Exception as e:
        return f"Error procesando la imagen: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python vision.py <ruta_imagen> [pregunta]")
        sys.exit(1)
        
    img_path = sys.argv[1]
    question = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Describe this image in detail."
    
    print(f"Analizando: {img_path}")
    print(f"Pregunta: {question}")
    print("\nRespuesta:")
    print(analyze_image(img_path, question))

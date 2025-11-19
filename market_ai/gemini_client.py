import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from django.shortcuts import render
from .forms import ChatForm

logger = logging.getLogger(__name__)

# ---------------- Cargar .env ----------------
load_dotenv()

# ---------------- Configuración del cliente ----------------
def configure_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("❌ La variable GEMINI_API_KEY no está definida en el archivo .env")
    
    # Configuración segura del cliente sin dejar expuesta la key
    genai.configure(api_key=api_key)

# ---------------- Modelo fijo ----------------
def get_first_text_model():
    try:
        configure_client()
        return "gemini-2.5-flash"
    except Exception as e:
        logger.warning(f"No se pudieron configurar modelos: {e}")
        return None

# ---------------- Generación de texto ----------------
def generate_text(prompt, max_output_tokens=500):
    model_name = get_first_text_model()
    if not model_name:
        return "El asistente no está disponible en este momento."

    config = GenerationConfig(
        max_output_tokens=max_output_tokens,
        temperature=0.7
    )

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt, generation_config=config)
        logger.debug(f"Respuesta cruda de Gemini: {response}")

        # Intentar obtener texto directo
        if hasattr(response, "text") and response.text:
            return response.text.strip()

        # Buscar en candidates si no vino directo
        if hasattr(response, "candidates") and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, "content") and candidate.content.parts:
                    texts = [p.text for p in candidate.content.parts if hasattr(p, "text")]
                    if texts:
                        return " ".join(texts).strip()

            finish_reason = getattr(response.candidates[0], "finish_reason", None)
            return f"El modelo finalizó sin texto (finish_reason={finish_reason})."

        return "No se generó ninguna respuesta."

    except Exception as e:
        logger.warning(f"Error al generar texto: {e}")
        return f"Error al generar texto: {e}"

# ---------------- Generación de embeddings ----------------
def embed_text(text, model="text-embedding-004"):
    try:
        configure_client()
        response = genai.embed_content(model=model, content=text)
        
        if hasattr(response, 'embedding'):
            return response.embedding
        
        return response
    except Exception as e:
        logger.warning(f"Error al generar embedding: {e}")
        return None

# ---------------- Vista del chat ----------------
def chat_view(request):
    history = []
    form = ChatForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user_message = form.cleaned_data['message']
        history.append({'user': user_message, 'ai': ''})

        ai_response = generate_text(user_message)
        history[-1]['ai'] = ai_response

    return render(request, 'chat.html', {'form': form, 'history': history})

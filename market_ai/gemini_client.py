import os
import logging
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from django.shortcuts import render
from .forms import ChatForm

logger = logging.getLogger(__name__)

# ---------------- Configuración del cliente ----------------
def configure_client():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("No se encontró GEMINI_API_KEY ni GOOGLE_API_KEY en las variables de entorno.")
    genai.configure(api_key=api_key)

# ---------------- Modelo fijo: Gemini 2.0 Flash ----------------
def get_first_text_model():
    try:
        configure_client()
        modelos = genai.list_models()
        text_models = [m.name for m in modelos if "2.0-flash" in m.name]
        return text_models[0] if text_models else None
    except Exception as e:
        logger.warning(f"No se pudieron listar modelos: {e}")
        return None
    

# ---------------- Generación de texto ----------------
def generate_text(prompt, max_output_tokens=200): 
    model_name = get_first_text_model()
    if not model_name:
        return "El asistente no está disponible en este momento."

    config = GenerationConfig(
        max_output_tokens= max_output_tokens,
        temperature=0.7

    )

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt, generation_config=config)
        logger.debug(f"Respuesta cruda de Gemini: {response}")

        if hasattr(response, 'text') and response.text:
            return response.text
        elif hasattr(response, 'candidates') and response.candidates:
            parts = response.candidates[0].content.parts
            if parts and hasattr(parts[0], 'text'):
                return parts[0].text
        return "El asistente no pudo generar una respuesta."
    except Exception as e:
        logger.warning(f"Error al generar texto: {e}")
        return "El asistente no está disponible en este momento."

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

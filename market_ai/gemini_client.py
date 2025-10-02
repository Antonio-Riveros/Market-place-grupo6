import os
import logging
from google import genai
from google.genai import types
from django.shortcuts import render
from .forms import ChatForm

logger = logging.getLogger(__name__)

# ---------------- Cliente GenAI ----------------
_client = None

def get_client():
    """
    Crea un cliente genai usando API key desde variables de entorno.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("No se encontró GEMINI_API_KEY ni GOOGLE_API_KEY en las variables de entorno.")
    return genai.Client(api_key=api_key)

def client():
    global _client
    if _client is None:
        _client = get_client()
    return _client

# ---------------- Modelos ----------------
def get_first_text_model():
    """
    Obtiene el primer modelo compatible con generación de texto.
    Filtra los modelos que contienen 'flash' o 'pro'.
    """
    c = client()
    try:
        modelos = c.models.list()
        text_models = [m.name for m in modelos if "flash" in m.name or "pro" in m.name]
        return text_models[0] if text_models else None
    except Exception as e:
        logger.warning(f"No se pudieron listar modelos: {e}")
        return None

# ---------------- Generación de texto ----------------
def generate_text(prompt, max_output_tokens=300):
    """
    Genera texto usando el primer modelo de texto válido.
    Si hay error o se supera la cuota, devuelve mensaje genérico.
    """
    model = get_first_text_model()
    if not model:
        return "El asistente no está disponible en este momento."

    config = types.GenerateContentConfig(
        max_output_tokens=max_output_tokens,
        temperature=0.7
    )
    try:
        response = client().models.generate_content(model=model, contents=prompt, config=config)
        if hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'candidates') and response.candidates:
            return response.candidates[0].content.parts[0].text
        else:
            return "El asistente no pudo generar una respuesta."
    except Exception as e:
        logger.warning(f"Error al generar texto: {e}")
        return "El asistente no está disponible en este momento."

# ---------------- Generación de embeddings ----------------
def embed_text(text, model="text-embedding-004"):
    """
    Genera embedding de un texto.
    """
    c = client()
    try:
        response = c.models.embed_content(model=model, contents=text)
        if hasattr(response, 'embeddings'):
            embeddings = response.embeddings
            if isinstance(embeddings, list) and len(embeddings) > 0:
                return embeddings[0].values if hasattr(embeddings[0], 'values') else embeddings[0]
            return embeddings
        return response
    except Exception as e:
        logger.warning(f"Error al generar embedding: {e}")
        return None

# ---------------- Vista del chat ----------------
def chat_view(request):
    """
    Vista del chat. La conversación se reinicia cada recarga de página.
    """
    history = []  # Siempre inicia vacía

    form = ChatForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user_message = form.cleaned_data['message']
        history.append({'user': user_message, 'ai': ''})

        # Generar respuesta del asistente
        ai_response = generate_text(user_message)
        history[-1]['ai'] = ai_response

    return render(request, 'chat.html', {'form': form, 'history': history})

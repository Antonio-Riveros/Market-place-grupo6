from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .forms import PriceSuggestForm, ChatForm
from .gemini_client import generate_text, embed_text
from market.models import Product
from .models import ProductEmbedding
import numpy as np

def price_suggest(request):
    sugerencia = None
    if request.method == "POST":
        form = PriceSuggestForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # PROMPT MEJORADO con contexto argentino y análisis profundo
            prompt = f"""
            Eres un experto en precios de mercado argentino con conocimiento en comercio electrónico.
            
            ANALIZA este producto para sugerir un precio óptimo:
            
            📦 PRODUCTO:
            - Título: {data['title']}
            - Descripción: {data['description']}
            - Marca: {data['marca']}
            - Precio actual: {data.get('current_price', 'No especificado')}
            
            🎯 CRITERIOS DE ANÁLISIS:
            1. Valor real basado en características y calidad
            2. Competitividad en el mercado argentino
            3. Percepción de valor del consumidor local
            4. Rentabilidad para el vendedor
            
            📊 FORMATO DE RESPUESTA OBLIGATORIO:
            PRECIO_SUGERIDO: [número entero sin puntos ni comas]
            RAZÓN: [2-3 frases explicando el análisis]
            TIPO: [Premium | Competitivo | Económico | Oferta]
            
            Ejemplo:
            PRECIO_SUGERIDO: 15000
            RAZÓN: El precio considera la calidad de materiales y la demanda estable en el rubro. Está 15% bajo el promedio de marcas similares.
            TIPO: Competitivo
            """
            
            respuesta = generate_text(prompt, max_output_tokens=200)
            sugerencia = respuesta
    else:
        form = PriceSuggestForm()
    
    return render(request, "price_suggest.html", {
        "form": form, 
        "sugerencia": sugerencia
    })

def ai_chat(request):
    # Limpiar chat si se presiona el botón
    if request.method == "POST" and "clear_chat" in request.POST:
        request.session["ai_chat_history"] = []
        request.session.modified = True
        form = ChatForm()
        return render(request, "ai_chat.html", {"form": form, "history": []})

    # Inicializamos historial en sesión si no existe
    if "ai_chat_history" not in request.session:
        request.session["ai_chat_history"] = []

    history = request.session["ai_chat_history"]

    if request.method == "POST" and "message" in request.POST:
        form = ChatForm(request.POST)
        if form.is_valid():
            user_msg = form.cleaned_data["message"]

            # PROMPT MEJORADO con personalidad definida y contexto marketplace
            system_prompt = """
            Eres "MateBot", un asistente virtual especializado en el marketplace argentino. 

            TU PERSONALIDAD:
            - Amable y cercano, como un amigo que sabe de compras
            - Usa modismos argentinos ocasionales (che, dale, etc.)
            - Práctico y orientado a soluciones
            - Conocedor de precios y tendencias locales

            ÁREAS DE ESPECIALIDAD:
            🛒 Cómo publicar productos efectivamente
            💰 Estrategias de precios y promociones
            📦 Logística y envíos en Argentina
            🎯 Cómo atraer más compradores
            🔍 Encontrar productos específicos

            Si no sabés algo, se honesto y ofrecé ayudar de otra forma.
            Mantené las respuestas útiles y centradas en el marketplace.
            """

            # Construir contexto de conversación
            conversation_context = system_prompt + "\n\nCONTEXTO DE CONVERSACIÓN:\n"
            
            # Incluir últimos 6 mensajes para mejor contexto
            for turn in history[-6:]:
                conversation_context += f"Usuario: {turn['user']}\nMateBot: {turn['ai']}\n"
            
            conversation_context += f"Usuario: {user_msg}\nMateBot: "

            ai_resp = generate_text(conversation_context, max_output_tokens=250)

            # Guardar en sesión (limitar a 12 mensajes máximo)
            history.append({"user": user_msg, "ai": ai_resp})
            if len(history) > 12:
                history = history[-12:]
            
            request.session["ai_chat_history"] = history
            request.session.modified = True
            
            # Resetear el formulario para nuevo mensaje
            form = ChatForm()
    else:
        form = ChatForm()

    return render(request, "ai_chat.html", {
        "form": form, 
        "history": history
    })

def recommend_similar(request, pk):
    """Sistema de recomendaciones mejorado con análisis semántico"""
    producto = get_object_or_404(Product, pk=pk, active=True)
    
    try:
        # Intentar usar embeddings guardados
        target = producto.embedding.vector
    except Exception:
        # Si no hay embedding, generarlo en tiempo real
        text = f"{producto.title}. {producto.description or ''}. Categoría: {producto.category}"
        target = embed_text(text)
        
        # Guardar el embedding para futuras recomendaciones
        if target:
            ProductEmbedding.objects.get_or_create(
                product=producto,
                defaults={'vector': target}
            )

    # Búsqueda de productos similares con filtros mejorados
    candidates = ProductEmbedding.objects.exclude(product=producto).select_related('product')
    
    # Filtrar solo productos activos y disponibles
    candidates = [c for c in candidates if c.product.active and c.product.stock > 0]
    
    if not candidates:
        # Fallback: búsqueda por categoría y palabras clave
        similar_products = Product.objects.filter(
            Q(category=producto.category) | 
            Q(title__icontains=producto.title.split()[0]) if producto.title else Q(),
            active=True,
            stock__gt=0
        ).exclude(id=producto.id)[:6]
        
        return render(request, "market_ai/recommendations.html", {
            "product": producto, 
            "recommended": similar_products,
            "method": "búsqueda por categoría"
        })

    # Cálculo de similitud con numpy optimizado
    results = []
    tvec = np.array(target, dtype=float)
    
    for candidate in candidates:
        cvec = np.array(candidate.vector, dtype=float)
        
        # Similitud coseno con manejo de errores
        try:
            norm_t = np.linalg.norm(tvec)
            norm_c = np.linalg.norm(cvec)
            
            if norm_t > 0 and norm_c > 0:
                cosine_sim = np.dot(tvec, cvec) / (norm_t * norm_c)
                results.append((candidate.product, float(cosine_sim)))
        except Exception:
            continue

    # Ordenar y tomar los mejores
    results.sort(key=lambda x: x[1], reverse=True)
    top_products = [product for product, score in results[:8] if score > 0.3]  # Filtro de similitud mínima
    
    # Si no hay suficientes similares, completar con productos de misma categoría
    if len(top_products) < 4:
        category_fallback = Product.objects.filter(
            category=producto.category,
            active=True,
            stock__gt=0
        ).exclude(id=producto.id)[:6]
        top_products.extend(category_fallback)
    
    # Eliminar duplicados
    seen_ids = set()
    unique_products = []
    for product in top_products[:6]:  # Máximo 6 recomendaciones
        if product.id not in seen_ids:
            seen_ids.add(product.id)
            unique_products.append(product)

    return render(request, "market_ai/recommendations.html", {
        "product": producto, 
        "recommended": unique_products,
        "method": "IA por similitud semántica"
    })

# NUEVA FUNCIÓN: Análisis de competitividad de precios
@login_required
def price_competitiveness_analysis(request, product_id):
    """Analiza qué tan competitivo es un precio vs productos similares en la plataforma"""
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    
    # Encontrar productos similares en la misma categoría
    similar_products = Product.objects.filter(
        category=product.category,
        active=True
    ).exclude(id=product.id)[:10]
    
    if similar_products:
        avg_price = sum(p.price for p in similar_products) / len(similar_products)
        price_position = "ALTO" if product.price > avg_price * 1.2 else "BAJO" if product.price < avg_price * 0.8 else "MEDIO"
        
        prompt = f"""
        Como experto en precios de marketplace, analiza la competitividad de este producto:
        
        📊 CONTEXTO:
        - Producto: {product.title} a ${product.price}
        - Categoría: {product.category}
        - Precio promedio de 10 similares: ${avg_price:.2f}
        - Posición relativa: {price_position}
        
        🎯 DA UN ANÁLISIS CON:
        1. Evaluación de competitividad (Alta/Media/Baja)
        2. Razón principal del posicionamiento
        3. Recomendación específica (mantener, subir, bajar)
        4. Estrategia sugerida
        
        Sé directo y práctico para el vendedor.
        """
        
        analysis = generate_text(prompt, max_output_tokens=250)
    else:
        analysis = "No hay suficientes productos similares para comparar en este momento."
    
    return render(request, "market_ai/price_analysis.html", {
        "product": product,
        "analysis": analysis,
        "similar_count": len(similar_products)
    })
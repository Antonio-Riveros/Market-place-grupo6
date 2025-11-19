from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from decimal import Decimal
from .forms import PriceSuggestForm, ChatForm
from .gemini_client import generate_text, embed_text
from market.models import Product
from .models import ProductEmbedding
import math

def price_suggest(request):
    sugerencia = None
    productos_sugeridos = []
    productos_disponibles = []
    
    if request.method == "POST":
        form = PriceSuggestForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            budget = data['budget']
            meal_type = data['meal_type']
            preferences = data['preferences']
            
            # Convertir a float para las operaciones
            budget_float = float(budget)
            
            # Buscar productos que estén dentro del presupuesto
            products = Product.objects.filter(
                active=True,
                price__lte=budget_float
            ).order_by('price')
            
            productos_disponibles = list(products[:15])
            productos_sugeridos = productos_disponibles
            
            if productos_disponibles:
                # Construir lista de productos para el prompt
                product_list = "\n".join([f"- {p.title}: ${p.price}" for p in productos_disponibles])
                
                # Prompt más simple y directo
                prompt = (
                    f"Con un presupuesto de ${budget} para {meal_type}, "
                    f"y con estos productos disponibles:\n\n{product_list}\n\n"
                    f"Sugerí 2-3 comidas simples que pueda preparar. "
                    f"Cada comida debe usar uno o más productos de la lista "
                    f"y el costo total no debe superar ${budget}. "
                    f"Incluí el nombre de la comida, los productos usados y el costo total. "
                    f"Sé práctico y realista."
                )
                
                try:
                    respuesta = generate_text(prompt, max_output_tokens=500)
                    if "Error al generar texto" not in respuesta:
                        sugerencia = respuesta
                    else:
                        # Si hay error, generar sugerencias básicas manualmente
                        sugerencia = generar_sugerencias_manuales(productos_disponibles, budget_float, meal_type)
                except Exception as e:
                    # Fallback a sugerencias manuales
                    sugerencia = generar_sugerencias_manuales(productos_disponibles, budget_float, meal_type)
            
    else:
        form = PriceSuggestForm()
    
    return render(request, "price_suggest.html", {
        "form": form, 
        "sugerencia": sugerencia,
        "productos_sugeridos": productos_sugeridos,
        "productos_disponibles": productos_disponibles
    })

def generar_sugerencias_manuales(productos, presupuesto, tipo_comida):
    """Genera sugerencias manuales cuando la IA falla"""
    sugerencias = []
    
    # Agrupar productos por tipo
    frutas_verduras = [p for p in productos if any(word in p.title.lower() for word in 
                      ['apple', 'pepper', 'cucumber', 'tomato', 'lettuce', 'banana', 'orange', 'fruit', 'vegetable'])]
    proteinas = [p for p in productos if any(word in p.title.lower() for word in 
                ['egg', 'steak', 'fish', 'chicken', 'meat', 'beef', 'pork'])]
    basicos = [p for p in productos if any(word in p.title.lower() for word in 
              ['oil', 'rice', 'bread', 'salt', 'sugar', 'flour', 'pasta'])]
    
    # Sugerencia 1: Ensalada simple
    if len(frutas_verduras) >= 2:
        ingredientes = frutas_verduras[:2]
        total = sum(float(p.price) for p in ingredientes)
        if total <= presupuesto:
            sugerencias.append(
                f"🥗 Ensalada Fresca\n"
                f"Productos: {ingredientes[0].title} (${ingredientes[0].price}) + {ingredientes[1].title} (${ingredientes[1].price})\n"
                f"Total: ${total:.2f}\n"
                f"Preparación: Lava y corta los ingredientes, mezcla y sirve."
            )
    
    # Sugerencia 2: Plato con proteína
    if proteinas and frutas_verduras:
        proteina = proteinas[0]
        verdura = frutas_verduras[0]
        total = float(proteina.price) + float(verdura.price)
        if total <= presupuesto:
            sugerencias.append(
                f"🍲 {proteina.title} con {verdura.title}\n"
                f"Productos: {proteina.title} (${proteina.price}) + {verdura.title} (${verdura.price})\n"
                f"Total: ${total:.2f}\n"
                f"Preparación: Cocina la proteína y acompaña con la verdura fresca o cocida."
            )
    
    # Sugerencia 3: Opción económica
    productos_baratos = [p for p in productos if float(p.price) <= presupuesto * 0.3]
    if productos_baratos:
        producto = productos_baratos[0]
        sugerencias.append(
            f"🍎 {producto.title} individual\n"
            f"Producto: {producto.title} (${producto.price})\n"
            f"Total: ${producto.price}\n"
            f"Preparación: Disfruta este producto como snack o complemento de tu comida."
        )
    
    if sugerencias:
        return "💡 Sugerencias basadas en productos disponibles:\n\n" + "\n\n".join(sugerencias)
    else:
        return "📦 Con tu presupuesto puedes comprar estos productos individuales:"

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

            # Construimos prompt con últimos 4 turnos
            system = "Sos un asistente amablemente orientado a ayudar en un marketplace (publicar, comprar, trueque). Responde en español."
            accumulated = system + "\n\n"
            for turn in history[-4:]:
                accumulated += f"Usuario: {turn['user']}\nAsistente: {turn['ai']}\n"
            accumulated += f"Usuario: {user_msg}\nAsistente: "

            ai_resp = generate_text(accumulated)

            # Guardamos en sesión
            history.append({"user": user_msg, "ai": ai_resp})
            request.session["ai_chat_history"] = history
            request.session.modified = True
    else:
        form = ChatForm()

    return render(request, "ai_chat.html", {"form": form, "history": history})

def recommend_similar(request, pk):
    # recomienda productos similares por embeddings
    producto = get_object_or_404(Product, pk=pk, active=True)
    try:
        # intentamos usar embeddings guardados
        target = producto.embedding.vector
    except Exception:
        # si no hay embedding guardado, generamos en vuelo
        text = f"{producto.title}. {producto.description or ''}"
        target = embed_text(text)

    # calculo de similitud simple con todos los product embeddings
    candidates = ProductEmbedding.objects.exclude(product=producto)
    results = []
    import numpy as np
    tvec = np.array(target, dtype=float)
    for c in candidates:
        vec = np.array(c.vector, dtype=float)
        # coseno
        cos = float(np.dot(tvec, vec) / (np.linalg.norm(tvec) * np.linalg.norm(vec)))
        results.append((c.product, cos))
    results.sort(key=lambda x: x[1], reverse=True)
    top = [p for p,score in results[:6]]
    return render(request, "market_ai/recommendations.html", {"product": producto, "recommended": top})
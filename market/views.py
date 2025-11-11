import mercadopago
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Cart, CartItem
from .forms import ProductForm
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Product, Cart, CartItem
import tempfile
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse


def product_list(request):
    products = Product.objects.filter(active=True)

    # Obtener parámetros del GET
    category = request.GET.get('category')
    order = request.GET.get('order')

    # Filtrar por categoría si viene en GET
    if category:
        products = products.filter(category=category)

    # Ordenar por precio si viene en GET
    if order == "asc":
        products = products.order_by('price')
    elif order == "desc":
        products = products.order_by('-price')
    else:
        products = products.order_by("-created_at")  # Default: recientes primero

    # Obtener todas las categorías para el dropdown
    categories = Product.objects.values_list('category', flat=True).distinct()

    return render(
        request,
        "product_list.html",
        {
            "products": products,
            "categories": categories
        }
    )

#CREAR PRODUCTO 

@login_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            return redirect("market:productlist")
    else:
        form = ProductForm()
    return render(request, "product_form.html", {"form": form})

#EDITAR PRODUCTO 

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect("market:productlist")
    else:
        form = ProductForm(instance=product)
    return render(request, "product_form.html", {"form": form})

#ELIMINAR PRODUCTO

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    if request.method == "POST":
        product.active = False
        product.save()
        return redirect("market:productlist")
    return render(request, "product_confirm_delete.html", {"product": product})

#AGREGAR AL CARRITO

@login_required
def add_to_cart(request, product_id):
    """Agrega un producto al carrito. Soporta AJAX y GET."""
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    # Intentar obtener el item existente
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if created:
        # Si es nuevo, arranca con 1
        item.quantity = 1
    else:
        # Si ya existía, sumar 1
        item.quantity += 1

    item.save()

    # Si es solicitud AJAX (fetch)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.method == "GET":
        total_items = sum(i.quantity for i in cart.items.all())
        return JsonResponse({
            "success": True,
            "product": product.title,
            "quantity": item.quantity,
            "total_items": total_items
        })

    return redirect("market:view-cart")

@login_required
def cart_increase(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    item.quantity += 1
    item.save()
    return redirect("market:view-cart")


@login_required
def cart_decrease(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()
    return redirect("market:view-cart")


@login_required
def cart_remove(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    item.delete()
    return redirect("market:view-cart")


@login_required
def cart_summary(request):
    """Devuelve el contenido del carrito como HTML para el offcanvas."""
    cart, created = Cart.objects.get_or_create(user=request.user)
    html = render_to_string("partials/cart_offcanvas_content.html", {"cart": cart}, request)
    return JsonResponse({"html": html})




def cart_view(request):
    cart = Cart.objects.get(user=request.user)
    return render(request, "market/cart.html", {
        "cart": cart,
        "MERCADOPAGO_PUBLIC_KEY": settings.MERCADOPAGO_PUBLIC_KEY
    })

#VER CARRITO

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, "cart.html", {
        "cart": cart,
        "PUBLIC_KEY": settings.MERCADOPAGO_PUBLIC_KEY
    })

#MERCADO PAGO

@login_required
def create_preference_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    items = []
    for item in cart.items.all():
        items.append({
            "title": item.product.title,
            "quantity": item.quantity,
            "unit_price": float(item.product.price),
            "currency_id": "ARS",
        })

    preference_data = {
        "items": items,
        "back_urls": {
            "success": request.build_absolute_uri("/pago-exitoso/"),
            "failure": request.build_absolute_uri("/pago-fallido/"),
        },
        "auto_return": "approved",
    }

    preference = sdk.preference().create(preference_data)
    return JsonResponse({"init_point": preference["response"]["init_point"]})




def cart_data(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = [{
        "id": item.product.id,
        "title": item.product.title,
        "price": item.product.price,
        "quantity": item.quantity,
        "subtotal": item.subtotal()
    } for item in cart.items.all()]
    return JsonResponse({
        "items": items,
        "total": cart.total()
    })
      
@login_required
def generate_budget(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    if not cart.items.exists():
        return HttpResponseRedirect('/market/cart/')  # URL de tu carrito

    # Fechas
    today = timezone.now().date()
    valid_until = today + timezone.timedelta(days=4)

    # Renderizar HTML con datos del usuario y validez
    html = render_to_string('budget.html', {
        'cart': cart,
        'user': request.user,
        'today': today,
        'valid_until': valid_until,
    })

    # Generar PDF en memoria
    pdf_response = HttpResponse(content_type='application/pdf')
    pdf_response['Content-Disposition'] = 'inline; filename="presupuesto.pdf"'

    pdf_status = pisa.CreatePDF(src=html, dest=pdf_response)
    if pdf_status.err:
        return HttpResponse('Error al generar PDF', status=500)

    # Enviar PDF por correo al usuario
    if request.user.email:  # Verifica que el usuario tenga email
        email = EmailMessage(
            subject='Tu presupuesto de Market',
            body=f"Hola {request.user.get_full_name() or request.user.username},\n\n"
                 f"Adjuntamos tu presupuesto. Este presupuesto tiene validez hasta {valid_until}.",
            from_email=None,  # Usará DEFAULT_FROM_EMAIL de settings.py
            to=[request.user.email],
        )
        email.attach('presupuesto.pdf', pdf_response.content, 'application/pdf')
        email.send(fail_silently=False)

    return pdf_response



# @login_required
# def crear_preferencia_carrito(request):
#     # Obtener carrito
#     cart, _ = Cart.objects.get_or_create(user=request.user)

#     # Validar que haya productos
#     if not cart.items.exists():
#         return JsonResponse({"error": "El carrito está vacío."}, status=400)

#     # Preparar items para Mercado Pago y validar precios
#     items_mp = []
#     for item in cart.items.all():
#         if item.product.price is None or item.product.price <= 0:
#             return JsonResponse({
#                 "error": f"El producto {item.product.title} tiene un precio inválido."
#             }, status=400)

#         items_mp.append({
#             "title": item.product.title,
#             "quantity": int(item.quantity),
#             "unit_price": float(item.product.price),
#             "currency_id": "ARS"
#         })

#     # Datos de preferencia
#     preference_data = {
#         "items": items_mp,
#         "payer": {"email": "TESTUSER2929@testuser.com"},  # email de sandbox
#         "back_urls": {
#             "success": request.build_absolute_uri(reverse('market:payment-success')),
#             "failure": request.build_absolute_uri(reverse('market:payment-failure')),
#             "pending": request.build_absolute_uri(reverse('market:payment-pending')),
#         },
#         "auto_return": "approved",
#     }

#     # Inicializar SDK
#     mp = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

#     try:
#         # Crear preferencia
#         preference_response = mp.preference().create(preference_data)

#         # DEBUG: imprimir respuesta completa
#         print("🔍 preference_response completo:", preference_response)
#         print("🔹 items enviados a MP:", items_mp)

#         # Obtener init_point de forma segura
#         init_point = preference_response.get("response", {}).get("init_point")
#         if not init_point:
#             return JsonResponse({
#                 "error": "No se generó init_point",
#                 "response": preference_response
#             }, status=500)

#         # Retornar URL de pago
#         return JsonResponse({"init_point": init_point})

#     except Exception as e:
#         # Capturar cualquier error
#         print("❌ Error creando preferencia:", e)
#         return JsonResponse({"error": str(e)}, status=500)

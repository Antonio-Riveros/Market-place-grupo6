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
from django.views.decorators.http import require_http_methods

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
    """Agrega un producto al carrito."""
    product = get_object_or_404(Product, id=product_id)
    
    # ✅ Obtener carrito de forma segura
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
    
    # ✅ Lógica normal del carrito SIN bloqueo por sesión
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if created:
        item.quantity = 1
    else:
        item.quantity += 1
    
    item.save()

    # ✅ Debug actualizado
    print("=" * 50)
    print(f"🔍 DEBUG add_to_cart")
    print(f"👤 User: {request.user}")
    print(f"🛒 Cart ID: {cart.id}")
    print(f"📦 Product: {product.title} (ID: {product.id})")
    print(f"📊 New Quantity: {item.quantity}")
    print(f"📋 All items in cart: {list(cart.items.values_list('product__title', 'quantity'))}")
    print("=" * 50)

    total_items = sum(i.quantity for i in cart.items.all())
    
    return JsonResponse({
        "success": True,
        "product": product.title,
        "quantity": item.quantity,
        "total_items": total_items
    })
    
    
    
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
    
    # ✅ Debug para verificar eliminación
    print("🗑️ Producto eliminado del carrito:", product_id)
    print("📋 Carrito después de eliminar:", list(cart.items.values_list('product__title', 'quantity')))
    
    return redirect("market:view-cart")


@login_required
def cart_summary(request):
    """Devuelve el contenido del carrito como HTML para el offcanvas."""
    cart, created = Cart.objects.get_or_create(user=request.user)
    html = render_to_string("partials/cart_offcanvas_content.html", {"cart": cart}, request)
    return JsonResponse({"html": html})



@login_required
def view_cart(request):
    # ✅ Obtener carrito de forma segura
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
    
    # ✅ DEBUG IMPORTANTE
    print("=" * 50)
    print(f"🔍 DEBUG view_cart")
    print(f"👤 User: {request.user}")
    print(f"🛒 Cart ID: {cart.id}")
    print(f"📋 Items in cart: {list(cart.items.values_list('product__title', 'quantity'))}")
    print("=" * 50)
    
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




@login_required
def cart_data(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
    
    items = [{
        "id": item.product.id,
        "title": item.product.title,
        "price": float(item.product.price),  # Convertir a float para evitar problemas de serialización
        "quantity": item.quantity,
        "subtotal": float(item.subtotal())
    } for item in cart.items.all()]
    
    return JsonResponse({
        "items": items,
        "total": float(cart.total())
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


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





#VER CARRITO

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, "cart.html", {"cart": cart})


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
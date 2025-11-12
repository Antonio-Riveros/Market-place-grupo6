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
from django.db.models import Q
from django.contrib import messages


def product_list(request):
    # Solo mostrar productos activos en el catálogo general
    # Usamos select_related para optimizar la consulta del vendedor
    products = Product.objects.filter(active=True).select_related('seller')

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
        products = products.order_by("-created_at")

    # Obtener todas las categorías para el dropdown
    categories = Product.objects.values_list('category', flat=True).distinct()

    # Verificar si el usuario tiene productos inactivos
    has_inactive_products = False
    if request.user.is_authenticated:
        has_inactive_products = Product.objects.filter(
            seller=request.user, 
            active=False
        ).exists()

    return render(
        request,
        "product_list.html",
        {
            "products": products,
            "categories": categories,
            "has_inactive_products": has_inactive_products
        }
    )

# VISTA MIS PUBLICACIONES
@login_required
def my_products(request):
    status_filter = request.GET.get('status', 'all')
    
    # ✅ SI ES ADMIN, MOSTRAR TODOS LOS PRODUCTOS
    if request.user.username == 'AntonioA' or request.user.is_superuser:
        products = Product.objects.all()
    else:
        # Usuario normal solo ve sus productos
        products = Product.objects.filter(seller=request.user)
    
    # Aplicar filtro de estado
    if status_filter == 'active':
        products = products.filter(active=True)
    elif status_filter == 'inactive':
        products = products.filter(active=False)
    
    # ✅ ESTADÍSTICAS DIFERENTES PARA ADMIN
    if request.user.username == 'AntonioA' or request.user.is_superuser:
        stats = {
            'total': Product.objects.count(),
            'active': Product.objects.filter(active=True).count(),
            'inactive': Product.objects.filter(active=False).count(),
        }
    else:
        stats = {
            'total': Product.objects.filter(seller=request.user).count(),
            'active': Product.objects.filter(seller=request.user, active=True).count(),
            'inactive': Product.objects.filter(seller=request.user, active=False).count(),
        }
    
    return render(request, "my_products.html", {
        "products": products.order_by('-created_at'),
        "status_filter": status_filter,
        "stats": stats
    })

# CAMBIAR ESTADO INDIVIDUAL
@login_required
def product_toggle_status(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    
    if request.method == "POST":
        new_status = request.POST.get('status')
        # Convertir status a boolean para el campo active
        if new_status == 'active':
            product.active = True
        elif new_status == 'inactive':
            product.active = False
        
        product.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'new_status': 'active' if product.active else 'inactive',
                'product_id': product.id
            })
    
    return redirect("market:my-products")

# REACTIVACIÓN MASIVA MEJORADA
@login_required
def reactivate_all_inactive(request):
    if request.method == "POST":
        # Obtener los productos seleccionados del formulario
        products_to_reactivate = request.POST.getlist('products_to_reactivate')
        
        if products_to_reactivate:
            # Reactivar solo los productos seleccionados
            updated = Product.objects.filter(
                seller=request.user, 
                active=False,
                id__in=products_to_reactivate
            ).update(active=True)
            
            messages.success(request, f'✅ Se reactivaron {updated} productos correctamente.')
        else:
            messages.warning(request, '⚠️ No seleccionaste ningún producto para reactivar.')
        
        return redirect("market:my-products")
    
    # GET - Mostrar confirmación con checkboxes
    inactive_products = Product.objects.filter(
        seller=request.user, 
        active=False
    )
    
    return render(request, "reactivate_confirm.html", {
        "inactive_products": inactive_products
    })

# CREAR PRODUCTO 
@login_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.active = True  # Nuevo producto siempre activo
            product.save()
            return redirect("market:my-products")
    else:
        form = ProductForm()
    return render(request, "product_form.html", {"form": form})

# EDITAR PRODUCTO (con permisos de admin)
@login_required
def product_edit(request, pk):
    # Verificar si el usuario es admin o el vendedor
    if request.user.username == 'AntonioA' or request.user.is_superuser:
        # Admin puede editar cualquier producto
        product = get_object_or_404(Product, pk=pk)
    else:
        # Usuario normal solo puede editar sus productos
        product = get_object_or_404(Product, pk=pk, seller=request.user)
    
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            
            # Mensaje diferente para admin
            if request.user.username == 'AntonioA' and product.seller != request.user:
                messages.success(request, f'✅ Producto editado (como administrador)')
            else:
                messages.success(request, f'✅ Producto editado correctamente')
                
            return redirect("market:my-products")
    else:
        form = ProductForm(instance=product)
    return render(request, "product_form.html", {"form": product})

# Función helper para eliminar archivos de imagen
def delete_product_image(product):
    """Elimina el archivo de imagen del filesystem si existe"""
    if product.image:
        try:
            image_path = os.path.join(settings.MEDIA_ROOT, str(product.image))
            if os.path.isfile(image_path):
                os.remove(image_path)
                print(f"✅ Imagen eliminada: {image_path}")
        except Exception as e:
            print(f"❌ Error eliminando imagen: {e}")

# Y actualizar la función product_delete:
@login_required
def product_delete(request, pk):
    if request.user.username == 'AntonioA' or request.user.is_superuser:
        product = get_object_or_404(Product, pk=pk)
        is_admin_action = True
    else:
        product = get_object_or_404(Product, pk=pk, seller=request.user)
        is_admin_action = False
    
    if request.method == "POST":
        if is_admin_action:
            # ✅ ELIMINACIÓN COMPLETA para admin
            product_title = product.title
            # Primero eliminar la imagen del filesystem
            delete_product_image(product)
            # Luego eliminar el producto de la base de datos
            product.delete()
            messages.success(request, f'🗑️ Producto "{product_title}" eliminado permanentemente')
        else:
            product.active = False
            product.save()
            messages.success(request, f'✅ Producto "{product.title}" marcado como inactivo')
            
        return redirect("market:my-products")
    
    return render(request, "product_confirm_delete.html", {
        "product": product,
        "is_admin_action": is_admin_action
    })
@login_required
def admin_products(request):
    # Solo accesible para AntonioA o superusers
    if request.user.username != 'AntonioA' and not request.user.is_superuser:
        messages.error(request, '❌ No tienes permisos para acceder a esta página')
        return redirect("market:productlist")
    
    products = Product.objects.all().order_by('-created_at')
    
    # Filtros para admin
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'active':
        products = products.filter(active=True)
    elif status_filter == 'inactive':
        products = products.filter(active=False)
    
    return render(request, "admin_products.html", {
        "products": products,
        "status_filter": status_filter,
        "total_products": Product.objects.count(),
        "active_products": Product.objects.filter(active=True).count(),
        "inactive_products": Product.objects.filter(active=False).count(),
    })


# AGREGAR AL CARRITO - MEJORADO PARA VERIFICAR ESTADO
@login_required
def add_to_cart(request, product_id):
    """Agrega un producto al carrito."""
    product = get_object_or_404(Product, id=product_id)
    
    # ✅ VERIFICAR que el producto esté activo
    if not product.is_available():
        return JsonResponse({
            "success": False,
            "error": "Este producto no está disponible actualmente."
        })
    
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
    
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if created:
        item.quantity = 1
    else:
        item.quantity += 1
    
    item.save()

    total_items = sum(i.quantity for i in cart.items.all())
    
    return JsonResponse({
        "success": True,
        "product": product.title,
        "quantity": item.quantity,
        "total_items": total_items
    })

@login_required
def cart_increase(request, product_id):
    # ✅ MEJORA: Manejo seguro del carrito
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
        
    item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    item.quantity += 1
    item.save()
    
    # ✅ MEJORA: Soporte para AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'new_quantity': item.quantity,
            'subtotal': float(item.subtotal()),
            'total': float(cart.total())
        })
    return redirect("market:view-cart")

@login_required
def cart_decrease(request, product_id):
    # ✅ MEJORA: Manejo seguro del carrito
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
        
    item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
        deleted = False
    else:
        item.delete()
        deleted = True

    # ✅ MEJORA: Soporte para AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if deleted:
            return JsonResponse({
                'success': True,
                'deleted': True,
                'total': float(cart.total())
            })
        else:
            return JsonResponse({
                'success': True,
                'new_quantity': item.quantity,
                'subtotal': float(item.subtotal()),
                'total': float(cart.total())
            })
    return redirect("market:view-cart")

@login_required
def cart_remove(request, product_id):
    # ✅ MEJORA: Manejo seguro del carrito
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
        
    item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    item.delete()
    
    # ✅ MEJORA: Debug para verificar eliminación
    print("🗑️ Producto eliminado del carrito:", product_id)
    print("📋 Carrito después de eliminar:", list(cart.items.values_list('product__title', 'quantity')))

    # ✅ MEJORA: Soporte para AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'deleted': True,
            'total': float(cart.total())
        })
    return redirect("market:view-cart")

@login_required
def cart_summary(request):
    """Devuelve el contenido del carrito como HTML para el offcanvas."""
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
        
    html = render_to_string("partials/cart_offcanvas_content.html", {"cart": cart}, request)
    return JsonResponse({"html": html})

#VER CARRITO
@login_required
def view_cart(request):
    # ✅ MEJORA: Manejo seguro del carrito
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
    
    # ✅ MEJORA: Debug mejorado
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

#MERCADO PAGO - PRESERVADO COMPLETO
@login_required
def create_preference_cart(request):
    # ✅ MEJORA: Manejo seguro del carrito
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
        
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

# DATOS DEL CARRITO PARA AJAX - MEJORADO
@login_required
def cart_data(request):
    # ✅ MEJORA: Manejo seguro del carrito
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
    
    items = [{
        "id": item.product.id,
        "title": item.product.title,
        "price": float(item.product.price),  # ✅ Convertir a float para evitar problemas
        "quantity": item.quantity,
        "subtotal": float(item.subtotal())
    } for item in cart.items.all()]
    
    return JsonResponse({
        "items": items,
        "total": float(cart.total())  # ✅ Convertir a float
    })

# GENERAR PRESUPUESTO PDF - PRESERVADO COMPLETO  
@login_required
def generate_budget(request):
    # ✅ MEJORA: Manejo seguro del carrito
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
        
    if not cart.items.exists():
        return HttpResponseRedirect('/market/cart/')

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
    if request.user.email:
        email = EmailMessage(
            subject='Tu presupuesto de Market',
            body=f"Hola {request.user.get_full_name() or request.user.username},\n\n"
                 f"Adjuntamos tu presupuesto. Este presupuesto tiene validez hasta {valid_until}.",
            from_email=None,
            to=[request.user.email],
        )
        email.attach('presupuesto.pdf', pdf_response.content, 'application/pdf')
        email.send(fail_silently=False)

    return pdf_response
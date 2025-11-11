# pagos/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from django.contrib.auth import get_user_model
import mercadopago
from market.models import Cart

User = get_user_model()

class CrearPagoCarrito(APIView):
    """
    Crea la preferencia de pago de todo el carrito del usuario.
    Imprime por consola info de cada item para debugging.
    """

    def post(self, request):
        # Obtener carrito del usuario
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response({"error": "Carrito no encontrado"}, status=404)

        if not cart.items.exists():
            return Response({"error": "El carrito está vacío"}, status=400)

        items_mp = []
        print("===== DATOS DEL CARRITO =====")
        for item in cart.items.all():
            title = item.product.title
            quantity = item.quantity
            unit_price = float(item.product.price)

            # Validaciones básicas
            if not isinstance(quantity, int) or quantity <= 0:
                print(f"⚠️ WARNING: Quantity inválida para {title}: {quantity}, se corrige a 1")
                quantity = 1

            if unit_price <= 0:
                print(f"⚠️ WARNING: Precio inválido para {title}: {unit_price}, se corrige a 1")
                unit_price = 1.0

            # Aquí podés forzar que unit_price sea mayor que price original si querés
            print(f"Producto: {title}, Cantidad: {quantity}, Unit Price original: {unit_price},")

            items_mp.append({
                "title": title,
                "quantity": quantity,
                "unit_price": unit_price,
                "currency_id": "ARS",
            })

        # Crear preferencia Mercado Pago
        preference_data = {
            "items": items_mp,
            "payer": {"email": request.user.email or "test_buyer@example.com"},
            "back_urls": {
                "success": request.build_absolute_uri("/pago/exito/"),
                "failure": request.build_absolute_uri("/pago/error/"),
                "pending": request.build_absolute_uri("/pago/pendiente/"),
            },
            "auto_return": "approved",
        }

        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

        try:
            preference = sdk.preference().create(preference_data)
        except Exception as e:
            print("❌ ERROR Mercado Pago:", e)
            return Response({"error": "Error al crear preferencia", "detalle": str(e)}, status=500)

        # Debug completo de la respuesta
        print("RESPUESTA MERCADO PAGO:", preference)

        if "response" in preference and "init_point" in preference["response"]:
            return Response({"init_point": preference["response"]["init_point"]})
        else:
            return Response({"error": "No se generó init_point", "response": preference}, status=500)

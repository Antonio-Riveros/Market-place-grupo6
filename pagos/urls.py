from django.urls import path
from .views import CrearPagoCarrito
urlpatterns = [
    path("crear/", CrearPagoCarrito.as_view(), name="crear-pago-carrito"),
]

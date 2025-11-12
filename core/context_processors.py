# core/context_processors.py
from django.conf import settings

def mercadopago_keys(request):
    return {
        "MERCADOPAGO_PUBLIC_KEY": settings.MERCADOPAGO_PUBLIC_KEY
    }
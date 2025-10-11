# propiedades/templatetags/filtros.py
from django import template
from django.utils.timesince import timesince
from django.utils import timezone
import re


register = template.Library()

# --------------------------
# Formato de precio en pesos
# --------------------------
@register.filter
def formato_pesos(valor):
    """
    Convierte un número en formato de pesos argentinos.
    Ej: 1250000 -> $1.250.000
    """
    try:
        valor = int(valor)
        return f"${valor:,}".replace(",", ".")
    except (ValueError, TypeError):
        return valor

# --------------------------
# Formato de superficie
# --------------------------
@register.filter
def formato_metros(valor):
    """
    Convierte un número en formato de metros cuadrados.
    Ej: 120 -> 120 m²
    """
    try:
        return f"{valor} m²"
    except (ValueError, TypeError):
        return valor

# --------------------------
# Formato habitaciones y baños
# --------------------------
@register.filter
def formato_habitaciones(valor):
    try:
        return f"{valor} hab."
    except (ValueError, TypeError):
        return valor

@register.filter
def formato_banos(valor):
    try:
        return f"{valor} baños"
    except (ValueError, TypeError):
        return valor

# --------------------------
# Tiempo desde publicación
# --------------------------
@register.filter
def hace_cuanto(fecha):
    """
    Devuelve un string como 'Publicado hace 3 días'.
    """
    if fecha:
        return f"Publicado hace {timesince(fecha, timezone.now()).split(',')[0]}"
    return ""


@register.filter
def solo_numeros(valor):
    """
    Quita todo lo que no sea dígito.
    Ej: "+54 9 11 1234-5678" -> "5491112345678"
    """
    if not valor:
        return ""
    return re.sub(r'\D', '', str(valor))
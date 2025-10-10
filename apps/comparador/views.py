from django.shortcuts import render
from apps.propiedades.models import Propiedad

def comparar(request):
    ids = request.GET.getlist('ids')  # ?ids=1&ids=3
    propiedades = Propiedad.objects.filter(id__in=ids)
    return render(request, 'comparador/comparar.html', {'propiedades': propiedades})

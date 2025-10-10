from django.shortcuts import render
from apps.propiedades.models import Propiedad

def buscar(request):
    query = request.GET.get('q')
    resultados = Propiedad.objects.filter(titulo__icontains=query) if query else []
    return render(request, 'buscador/resultados.html', {'resultados': resultados, 'query': query})

def recomendadas(request):
    propiedades = Propiedad.objects.order_by('-fecha_publicacion')[:6]
    return render(request, 'buscador/recomendadas.html', {'propiedades': propiedades})

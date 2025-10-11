# core/views.py
from django.shortcuts import render

def nosotros(request):
    return render(request, 'core/nosotros.html')  # ajusta la ruta según tu template

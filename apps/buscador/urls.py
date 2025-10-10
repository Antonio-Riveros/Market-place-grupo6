# apps/buscador/urls.py
from django.urls import path
from . import views

urlpatterns = [
     path('', views.buscar, name='buscar'),
]

# apps/usuarios/urls.py
from django.urls import path
from . import views

app_name = 'usuarios'  # <- Esto define el namespace

urlpatterns = [
    path('perfil/', views.profile, name='perfil'),
    path('editar/', views.editar_perfil, name='editar_perfil'),
]

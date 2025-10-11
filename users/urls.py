# apps/usuarios/urls.py
from django.urls import path
from . import views
from .views import CambiarPasswordView

app_name = 'usuarios'  # <- Esto define el namespace

urlpatterns = [
    path('perfil/', views.profile, name='perfil'),
    path('editar/', views.editar_perfil, name='editar_perfil'),
    path('cambiar-password/', CambiarPasswordView.as_view(), name='password_change'),
    path('eliminar-cuenta/', views.eliminar_cuenta, name='eliminar_cuenta'),
    path('eliminar-cuenta/confirmar/', views.eliminar_cuenta_confirmar, name='eliminar_cuenta_confirmar'),
    path('cancelar-eliminacion/', views.cancelar_eliminacion, name='cancelar_eliminacion'),
    path('eliminar-ahora/', views.eliminar_ahora, name='eliminar_ahora'),
]

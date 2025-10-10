from django.urls import path
from . import views

urlpatterns = [
    path('agregar/', views.agregar_propiedad, name='agregar_propiedad'),  # Agregar propiedad
    path('<int:id>/', views.detalle_propiedad, name='detalle_propiedad'),  # Ver detalle
    path('<int:id>/eliminar/', views.eliminar_propiedad, name='eliminar_propiedad'),  # Eliminar propiedad
]

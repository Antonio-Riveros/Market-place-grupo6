from django.urls import path
from . import views

urlpatterns = [
    path('crear/', views.crear_propiedad, name='crear_propiedad'),
    path('editar/<int:pk>/', views.editar_propiedad, name='editar_propiedad'),
    path('borrar/<int:pk>/', views.borrar_propiedad, name='borrar_propiedad'),
    path('', views.listar_propiedades, name='listar_propiedades'),
    path('detalle/<int:pk>/', views.detalle_propiedad, name='detalle_propiedad'),
    path('mis-propiedades/', views.mis_propiedades, name='mis_propiedades'),
    path('configuracion/', views.configuracion, name='configuracion'),
]

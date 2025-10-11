from django.db import models
from django.contrib.auth.models import User

class Propiedad(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    ubicacion = models.CharField(max_length=200)
    habitaciones = models.IntegerField(default=0)
    banos = models.IntegerField(default=0)
    metros_cuadrados = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    telefono_contacto = models.CharField(max_length=20, null=True, blank=True, help_text="Número de WhatsApp del propietario")
    publicada_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='propiedades')
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo
class ImagenPropiedad(models.Model):
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='propiedades/')

    def __str__(self):
        return f"Imagen de {self.propiedad.titulo}"

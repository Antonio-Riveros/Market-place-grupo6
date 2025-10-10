from django.db import models
from django.contrib.auth.models import User

class Propiedad(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    ubicacion = models.CharField(max_length=200)
    metros_cuadrados = models.IntegerField()
    habitaciones = models.IntegerField()
    banos = models.IntegerField()
    imagen = models.ImageField(upload_to='propiedades/', blank=True, null=True)  # solo una vez
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    publicada_por = models.ForeignKey(User, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return self.titulo

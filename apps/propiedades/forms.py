from django import forms
from django.forms import inlineformset_factory
from .models import Propiedad, ImagenPropiedad

class PropiedadForm(forms.ModelForm):
    class Meta:
        model = Propiedad
        fields = [
            'titulo', 'descripcion', 'precio', 'ubicacion',
            'habitaciones', 'banos', 'metros_cuadrados',
            'telefono_contacto'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'telefono_contacto': forms.TextInput(attrs={'placeholder': '+54 9 11 1234 5678'}),
        }
class ImagenForm(forms.ModelForm):
    class Meta:
        model = ImagenPropiedad
        fields = ['imagen']

ImagenFormSet = inlineformset_factory(
    Propiedad, 
    ImagenPropiedad, 
    form=ImagenForm, 
    extra=5,
    min_num=1,
    validate_min=True,
    can_delete=True
)

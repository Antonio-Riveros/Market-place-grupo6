from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Profile

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'}),
        label="Contraseña"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control rounded-3'}),
        label="Repetir Contraseña"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control rounded-3'}),
            'email': forms.EmailInput(attrs={'class': 'form-control rounded-3'}),
        }

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if not password or not password2:
            raise ValidationError("Por favor completa ambos campos de contraseña")
        if password != password2:
            raise ValidationError("Las contraseñas no coinciden")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo ya está registrado")
        return email


class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
        }


class PerfilForm(forms.ModelForm):
    """Formulario para manejar el avatar del usuario"""
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        label=''  # Sin texto para evitar "Currently..."
    )

    class Meta:
        model = Profile
        fields = ['avatar']

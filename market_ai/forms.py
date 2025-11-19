from django import forms
from market.models import Product
from decimal import Decimal  
class PriceSuggestForm(forms.Form):
    budget = forms.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        label="Tu presupuesto",
        help_text="¿Cuánto dinero tenés para comer?",
        min_value=Decimal('0.01')
    )
    meal_type = forms.ChoiceField(
        choices=[
            ('almuerzo', 'Almuerzo'),
            ('cena', 'Cena'),
            ('cualquiera', 'Cualquiera')
        ],
        label="Tipo de comida",
        initial='cualquiera'
    )
    preferences = forms.CharField(
        widget=forms.TextInput(attrs={
            "placeholder": "Ej: vegetariano, sin gluten, rápido, saludable",
            "style": "width: 100%"
        }),
        required=False,
        label="Preferencias o restricciones",
        help_text="Separadas por comas"
    )
class ChatForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea(attrs={"rows":2}), label="Tu mensaje")

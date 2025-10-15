from django.urls import path, include
from . import views  # <-- core/views.py

app_name = "core"

urlpatterns = [
    path("home/", views.home, name="home"),
    path('login/', views.login_view, name='login'),
    path('tienda/', views.tienda, name='tienda'),
    path('', include('market.urls')),
]


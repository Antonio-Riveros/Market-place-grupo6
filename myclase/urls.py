from django.contrib import admin
from django.urls import path, include
from core.views import home
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", home, name="home"),
    path("accounts/", include("allauth.urls")),  
    path("market/", include("market.urls")),  
    path("profiles/", include("perfil.urls")), 
    path("ai/", include("market_ai.urls")),  
    path('accounts/', include('django.contrib.auth.urls')),  
    path('', include('core.urls')),
# ============Semana7=================================   
    path("", include("presence.urls")), #sesion activa
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
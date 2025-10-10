from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Propiedad
from .forms import PropiedadForm  # vamos a crear este formulario
from django.core.exceptions import PermissionDenied

def detalle_propiedad(request, id):
    propiedad = get_object_or_404(Propiedad, id=id)
    return render(request, 'propiedades/detalle.html', {'propiedad': propiedad})

@login_required
def agregar_propiedad(request):
    """
    Permite a cualquier usuario logueado agregar una propiedad.
    """
    if request.method == 'POST':
        form = PropiedadForm(request.POST, request.FILES)
        if form.is_valid():
            propiedad = form.save(commit=False)
            propiedad.publicada_por = request.user  # asigna quien publica
            propiedad.save()
            return redirect('index')
    else:
        form = PropiedadForm()

    return render(request, 'propiedades/agregar_propiedad.html', {'form': form})

def eliminar_propiedad(request, id):
    propiedad = get_object_or_404(Propiedad, id=id)
    
    # Verificamos permisos
    if request.user == propiedad.publicada_por or request.user.is_staff:
        propiedad.delete()
        return redirect('index')
    else:
        raise PermissionDenied("No tienes permiso para eliminar esta propiedad")
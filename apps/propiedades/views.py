from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import PropiedadForm, ImagenFormSet
from .models import Propiedad
from django.utils import timezone
from datetime import timedelta

# Crear propiedad
@login_required
def crear_propiedad(request):
    if request.method == 'POST':
        form = PropiedadForm(request.POST)
        formset = ImagenFormSet(request.POST, request.FILES)

        if form.is_valid():
            propiedad = form.save(commit=False)
            propiedad.publicada_por = request.user
            propiedad.save()

            formset = ImagenFormSet(request.POST, request.FILES, instance=propiedad)

            imagenes_validas = [f for f in formset.cleaned_data if f and not f.get('DELETE', False)]
            if len(imagenes_validas) < propiedad.habitaciones:
                messages.error(request, f'Debes subir al menos {propiedad.habitaciones} imágenes.')
            elif formset.is_valid():
                formset.save()
                messages.success(request, 'Propiedad creada correctamente.')
                return redirect('index')
    else:
        form = PropiedadForm()
        formset = ImagenFormSet()

    return render(request, 'propiedades/crear_propiedad.html', {'form': form, 'formset': formset})

# Editar propiedad
@login_required
def editar_propiedad(request, pk):
    propiedad = get_object_or_404(Propiedad, pk=pk)

    if propiedad.publicada_por != request.user:
        messages.error(request, 'No tienes permisos para editar esta propiedad.')
        return redirect('index')

    if request.method == 'POST':
        form = PropiedadForm(request.POST, instance=propiedad)
        formset = ImagenFormSet(request.POST, request.FILES, instance=propiedad)
        if form.is_valid() and formset.is_valid():
            propiedad = form.save()
            formset.save()
            messages.success(request, 'Propiedad actualizada correctamente.')
            return redirect('index')
    else:
        form = PropiedadForm(instance=propiedad)
        formset = ImagenFormSet(instance=propiedad)

    return render(request, 'propiedades/editar_propiedad.html', {'form': form, 'formset': formset})

# Eliminar propiedad
@login_required
def borrar_propiedad(request, pk):
    propiedad = get_object_or_404(Propiedad, pk=pk)

    if propiedad.publicada_por != request.user:
        messages.error(request, 'No tienes permisos para borrar esta propiedad.')
        return redirect('index')

    if request.method == 'POST':
        propiedad.delete()
        messages.success(request, 'Propiedad eliminada correctamente.')
        return redirect('index')

    return render(request, 'propiedades/borrar_propiedad.html', {'propiedad': propiedad})



def listar_propiedades(request):
    propiedades = Propiedad.objects.all().order_by('-fecha_publicacion')
    return render(request, 'propiedades/listar_propiedades.html', {'propiedades': propiedades})

def detalle_propiedad(request, pk):
    propiedad = get_object_or_404(Propiedad, pk=pk)
    return render(request, 'propiedades/detalle_propiedad.html', {'propiedad': propiedad})



@login_required
def mis_propiedades(request):
    propiedades = Propiedad.objects.filter(publicada_por=request.user)
    return render(request, 'propiedades/mis_propiedades.html', {'propiedades': propiedades})


@login_required
def configuracion(request):
    tiene_propiedades = Propiedad.objects.filter(publicada_por=request.user).exists()
    return render(request, 'configuracion.html', {'tiene_propiedades': tiene_propiedades})





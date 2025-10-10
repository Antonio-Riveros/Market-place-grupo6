from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from .forms import UserRegisterForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django.contrib.auth import logout

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            # Guardamos el usuario
            user = form.save(commit=False)

            # Generamos username automáticamente (nombre.apellido en minúsculas)
            first_name = form.cleaned_data.get('first_name').strip().lower()
            last_name = form.cleaned_data.get('last_name').strip().lower()
            username_base = f"{first_name}.{last_name}"
            username = username_base
            counter = 1
            # Evitar duplicados
            from django.contrib.auth.models import User
            while User.objects.filter(username=username).exists():
                username = f"{username_base}{counter}"
                counter += 1
            user.username = username

            # Guardar la contraseña correctamente
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Autenticamos y hacemos login
            login(request, user)

            messages.success(request, f"¡Cuenta creada! Tu usuario es {user.username}")
            return redirect('index')  # Cambia 'home' por la URL a la que quieras redirigir
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'users/perfil.html')

def editar_perfil(request):
    user = request.user  # Obtenemos el usuario logueado

    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Perfil actualizado correctamente!')
            return redirect('editar_perfil')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = UserChangeForm(instance=user)

    return render(request, 'users/editar_perfil.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')
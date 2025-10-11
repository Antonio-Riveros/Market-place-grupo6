from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from .forms import UserRegisterForm, EditarPerfilForm, PerfilForm
from .models import Profile
from django.contrib.auth import authenticate



# Registro de usuarios
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Generar username automáticamente
            first_name = form.cleaned_data.get('first_name').strip().lower()
            last_name = form.cleaned_data.get('last_name').strip().lower()
            username_base = f"{first_name}.{last_name}"
            username = username_base
            counter = 1
            while Profile.objects.filter(user__username=username).exists():
                username = f"{username_base}{counter}"
                counter += 1
            user.username = username

            user.set_password(form.cleaned_data['password'])
            user.save()

            login(request, user)
            messages.success(request, f"¡Cuenta creada! Tu usuario es {user.username}")
            return redirect('index')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})


# Perfil
@login_required
def profile(request):
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user)
    return render(request, 'users/perfil.html')


# Editar perfil (User + Profile)
@login_required
def editar_perfil(request):
    user = request.user
    perfil = user.profile

    if request.method == 'POST':
        user_form = EditarPerfilForm(request.POST, instance=user)
        perfil_form = PerfilForm(request.POST, request.FILES, instance=perfil)

        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()

            # Si el usuario marcó "Eliminar foto"
            if request.POST.get('eliminar_avatar'):
                perfil.avatar = 'avatars/default.png'
            else:
                if perfil_form.cleaned_data.get('avatar'):
                    perfil.avatar = perfil_form.cleaned_data.get('avatar')

            perfil.save()
            messages.success(request, '¡Perfil actualizado correctamente!')
            return redirect('usuarios:editar_perfil')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        user_form = EditarPerfilForm(instance=user)
        perfil_form = PerfilForm(instance=perfil)

    return render(request, 'users/editar_perfil.html', {
        'user_form': user_form,
        'perfil_form': perfil_form
    })


# Cerrar sesión
def logout_view(request):
    logout(request)
    return redirect('index')


# Cambiar contraseña
class CambiarPasswordView(PasswordChangeView):
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('usuarios:perfil')

    def form_valid(self, form):
        response = super().form_valid(form)
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, "Tu contraseña fue actualizada correctamente")
        return response



@login_required
def eliminar_cuenta(request):
    return render(request, 'users/eliminar_cuenta.html')

@login_required
def eliminar_cuenta_confirmar(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        user = request.user
        if authenticate(username=user.username, password=password):
            # Programar eliminación en 15 días
            from datetime import timedelta
            import datetime
            user.profile.eliminacion_programada = datetime.datetime.now() + timedelta(days=15)
            user.profile.save()
            messages.warning(request, 'Se ha programado la eliminación de tu cuenta en 15 días.')
            return redirect('configuracion')
        else:
            return render(request, 'users/eliminar_cuenta.html', {'mensaje': 'Contraseña incorrecta'})
    return redirect('configuracion')

@login_required
def cancelar_eliminacion(request):
    user = request.user
    if user.profile.eliminacion_programada:
        user.profile.eliminacion_programada = None
        user.profile.save()
        messages.success(request, 'Se ha cancelado la eliminación de tu cuenta.')
    return redirect('configuracion')




@login_required
def eliminar_ahora(request):
    user = request.user
    # Eliminamos todos los datos relacionados si los tenés, ejemplo propiedades
    user.propiedades.all().delete()  # elimina todas las propiedades del usuario
    # Eliminamos el perfil si tenés uno
    if hasattr(user, 'profile'):
        user.profile.delete()
    # Finalmente eliminamos al usuario
    user.delete()
    logout(request)
    messages.success(request, 'Tu cuenta y todos tus datos han sido eliminados permanentemente.')
    return redirect('index')
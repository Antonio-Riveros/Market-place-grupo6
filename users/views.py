from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from .forms import UserRegisterForm, EditarPerfilForm, PerfilForm
from .models import Profile

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

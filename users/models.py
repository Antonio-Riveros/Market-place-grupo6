from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"

    def save(self, *args, **kwargs):
        # Asegura siempre un avatar por defecto
        if not self.avatar:
            self.avatar = 'avatars/default.png'
        super().save(*args, **kwargs)


# 🔔 Señales para crear o actualizar automáticamente el perfil
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # Evita error si no tiene profile (por usuarios viejos)
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            Profile.objects.create(user=instance)

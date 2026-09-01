from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profil


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def creer_ou_mettre_a_jour_profil(sender, instance, created, **kwargs):
    """
    Crée automatiquement un Profil pour tout nouvel utilisateur Django.
    Les super-utilisateurs (créés via createsuperuser) reçoivent le rôle
    Administrateur ; tous les autres reçoivent Agent par défaut (le rôle
    peut ensuite être modifié par un administrateur depuis la gestion des
    utilisateurs).
    """
    if created:
        role = Profil.ADMINISTRATEUR if instance.is_superuser else Profil.AGENT
        Profil.objects.get_or_create(utilisateur=instance, defaults={"role": role})
    elif instance.is_superuser:
        # S'assure qu'un super-utilisateur promu ait toujours le rôle Administrateur
        Profil.objects.filter(utilisateur=instance).exclude(role=Profil.ADMINISTRATEUR).update(
            role=Profil.ADMINISTRATEUR
        )

from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .models import Profil


def _profil_a_le_role(user, roles):
    if user.is_superuser:
        return True
    profil = getattr(user, "profil", None)
    return bool(profil and profil.role in roles)


def role_required(*roles):
    """
    Décorateur combinant l'authentification et le contrôle de rôle.

    Exemple :
        @role_required(Profil.ADMINISTRATEUR, Profil.AGENT)
        def ma_vue(request): ...

    - Un utilisateur non connecté est redirigé vers la page de connexion.
    - Un utilisateur connecté sans le rôle requis reçoit une erreur 403.
    """

    def decorateur(vue):
        @wraps(vue)
        def enveloppe(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not _profil_a_le_role(request.user, roles):
                raise PermissionDenied(
                    "Vous n'avez pas les droits nécessaires pour accéder à cette page."
                )
            return vue(request, *args, **kwargs)

        return enveloppe

    return decorateur


# Raccourcis pratiques
agent_requis = role_required(Profil.ADMINISTRATEUR, Profil.AGENT)
administrateur_requis = role_required(Profil.ADMINISTRATEUR)

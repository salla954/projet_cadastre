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


def peut_acceder_rubrique(user, specialite_associee):
    """Un administrateur, ou un agent Généraliste/Accueil (ou dont le profil
    manquerait, cas limite d'un compte créé hors du parcours normal de
    l'appli), a accès à toutes les rubriques. Un agent Cadastre ou Fiscalité
    n'a accès qu'à la rubrique de sa spécialité."""
    if user.is_superuser:
        return True
    profil = getattr(user, "profil", None)
    if profil is None:
        return True
    if profil.role == Profil.ADMINISTRATEUR:
        return True
    if profil.specialite in (Profil.GENERALISTE, Profil.SPECIALITE_ACCUEIL, ""):
        return True
    return profil.specialite == specialite_associee


def rubrique_requise(specialite_associee):
    """Comme role_required(ADMINISTRATEUR, AGENT), mais restreint en plus
    l'accès à la rubrique (Cadastre ou Fiscalité) correspondant à la
    spécialité de l'agent — un agent Fiscalité n'a par exemple pas accès aux
    pages réservées à la rubrique Cadastre, et réciproquement."""

    def decorateur(vue):
        @wraps(vue)
        def enveloppe(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not _profil_a_le_role(request.user, (Profil.ADMINISTRATEUR, Profil.AGENT)):
                raise PermissionDenied(
                    "Vous n'avez pas les droits nécessaires pour accéder à cette page."
                )
            if not peut_acceder_rubrique(request.user, specialite_associee):
                raise PermissionDenied(
                    "Cette page relève d'une autre rubrique (Cadastre ou Fiscalité) que "
                    "celle de votre spécialité. Contactez un administrateur si cela ne "
                    "devrait pas être le cas."
                )
            return vue(request, *args, **kwargs)

        return enveloppe

    return decorateur


cadastre_agent_requis = rubrique_requise(Profil.SPECIALITE_CADASTRE)
fiscalite_agent_requis = rubrique_requise(Profil.SPECIALITE_FISCALITE)

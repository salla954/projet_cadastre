from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from demarches.models import Dossier, RendezVous

from .decorators import administrateur_requis
from .forms import CreationUtilisateurForm, ModifierRoleForm
from .models import Profil


class ConnexionView(auth_views.LoginView):
    template_name = "appcadastre/connexion.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        # Le tableau de bord doit toujours être la première page vue après
        # connexion, pour un agent comme pour un administrateur — même si un
        # paramètre "next" (retour à la page d'origine) pointait ailleurs.
        return reverse_lazy("dashboard:accueil")

    def _est_ajax(self):
        return self.request.headers.get("X-Requested-With") == "XMLHttpRequest"

    def form_valid(self, form):
        if self._est_ajax():
            auth_login(self.request, form.get_user())
            return JsonResponse({"succes": True, "redirection": self.get_success_url()})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self._est_ajax():
            return JsonResponse(
                {"succes": False, "erreur": "Identifiant ou mot de passe incorrect."},
                status=400,
            )
        return super().form_invalid(form)


class DeconnexionView(auth_views.LogoutView):
    pass


@administrateur_requis
def liste_utilisateurs(request):
    """Gestion des comptes : réservé aux administrateurs."""
    utilisateurs = User.objects.select_related("profil").order_by("username")
    return render(request, "appcadastre/liste_utilisateurs.html", {
        "utilisateurs": utilisateurs,
    })


@administrateur_requis
def creer_utilisateur(request):
    if request.method == "POST":
        form = CreationUtilisateurForm(request.POST)
        if form.is_valid():
            utilisateur = form.save()
            messages.success(
                request,
                f"Le compte « {utilisateur.username} » a été créé avec le rôle "
                f"{utilisateur.profil.get_role_display()}.",
            )
            return redirect("appcadastre:liste_utilisateurs")
    else:
        form = CreationUtilisateurForm()
    return render(request, "appcadastre/creer_utilisateur.html", {"form": form})


@administrateur_requis
def modifier_utilisateur(request, pk):
    utilisateur = get_object_or_404(User.objects.select_related("profil"), pk=pk)
    profil, _ = Profil.objects.get_or_create(utilisateur=utilisateur)

    if request.method == "POST":
        form = ModifierRoleForm(request.POST, initial={
            "role": profil.role, "actif": utilisateur.is_active,
        })
        if form.is_valid():
            if utilisateur == request.user and (
                form.cleaned_data["role"] != Profil.ADMINISTRATEUR
                or not form.cleaned_data["actif"]
            ):
                messages.error(
                    request,
                    "Vous ne pouvez pas retirer vos propres droits d'administrateur "
                    "ou désactiver votre propre compte.",
                )
                return redirect("appcadastre:modifier_utilisateur", pk=utilisateur.pk)
            profil.role = form.cleaned_data["role"]
            profil.specialite = form.cleaned_data.get("specialite") or Profil.GENERALISTE
            utilisateur.is_active = form.cleaned_data["actif"]
            utilisateur.is_staff = profil.role == Profil.ADMINISTRATEUR
            utilisateur.is_superuser = profil.role == Profil.ADMINISTRATEUR
            utilisateur.save()
            profil.save()
            profil.communes_attribuees.set(form.cleaned_data.get("communes_attribuees") or [])
            messages.success(request, f"Le compte « {utilisateur.username} » a été mis à jour.")
            return redirect("appcadastre:liste_utilisateurs")
    else:
        form = ModifierRoleForm(initial={
            "role": profil.role, "actif": utilisateur.is_active,
            "specialite": profil.specialite,
            "communes_attribuees": profil.communes_attribuees.all(),
        })

    return render(request, "appcadastre/modifier_utilisateur.html", {
        "form": form, "utilisateur_cible": utilisateur,
    })


# Description statique des accès accordés par chaque rôle. Tenue à jour
# manuellement (les rôles eux-mêmes sont fixes, définis dans Profil.ROLE_CHOICES) ;
# sert de documentation lisible pour les administrateurs, en complément de la
# liste des comptes.
DESCRIPTION_ROLES = [
    {
        "code": Profil.ADMINISTRATEUR,
        "libelle": "Administrateur",
        "badge": "badge-ocre",
        "icone": "🛡️",
        "description": (
            "Accès complet à la plateforme : l'ensemble du back-office métier, "
            "ainsi que la gestion des comptes et la supervision de la plateforme."
        ),
        "acces": [
            "Tableau de bord, carte et statistiques",
            "Parcelles et taxes foncières (consultation, émission, paiement)",
            "Dossiers déposés et rendez-vous",
            "Gestion du contenu public (actualités, guide du visiteur)",
            "Gestion des comptes utilisateurs et des rôles",
            "Journal d'activité",
            "Administration Django (django-admin)",
        ],
    },
    {
        "code": Profil.AGENT,
        "libelle": "Agent",
        "badge": "badge-vert",
        "icone": "🧑‍💼",
        "description": (
            "Accès au back-office métier du cadastre et de la fiscalité foncière, "
            "sans droit sur les comptes utilisateurs ni sur le journal d'activité."
        ),
        "acces": [
            "Tableau de bord, carte et statistiques",
            "Parcelles et taxes foncières (consultation, émission, paiement)",
            "Dossiers déposés et rendez-vous",
            "Gestion du contenu public (actualités, guide du visiteur)",
        ],
    },
    {
        "code": Profil.VISITEUR,
        "libelle": "Visiteur",
        "badge": "badge-gris",
        "icone": "🌐",
        "description": (
            "Grand public. Aucune authentification requise : accès uniquement "
            "aux pages publiques du site."
        ),
        "acces": [
            "Accueil, actualités et guide du visiteur",
            "Consultation d'une parcelle par référence",
            "Simulateur de taxe foncière",
            "Dépôt et suivi d'un dossier, prise de rendez-vous",
        ],
    },
]


@administrateur_requis
def apercu_roles(request):
    """Vue d'ensemble des rôles : ce que chacun permet de faire, et qui en
    dispose. Vient compléter la liste des comptes (utilisateur par utilisateur)
    par une lecture centrée sur le rôle — avec, pour les agents, la mission
    confiée (spécialité, communes) et la charge de dossiers/rendez-vous en cours."""
    utilisateurs_par_role = {}
    for utilisateur in (
        User.objects.select_related("profil")
        .prefetch_related("profil__communes_attribuees")
        .order_by("username")
    ):
        if not hasattr(utilisateur, "profil"):
            # Compte créé hors du parcours normal de l'appli (ex. createsuperuser
            # en ligne de commande) : on lui crée un profil par défaut à la volée
            # plutôt que de faire planter la page.
            profil, _ = Profil.objects.get_or_create(utilisateur=utilisateur)
            utilisateur.profil = profil
        role = utilisateur.profil.role
        if utilisateur.is_superuser and role != Profil.ADMINISTRATEUR:
            role = Profil.ADMINISTRATEUR
        utilisateurs_par_role.setdefault(role, []).append(utilisateur)

    # Charge de travail en cours par agent (dossiers déposés/en cours d'instruction,
    # rendez-vous demandés/confirmés), pour repérer d'un coup d'œil qui est surchargé.
    charge_dossiers = dict(
        Dossier.objects.filter(statut__in=[Dossier.DEPOSE, Dossier.EN_COURS])
        .values_list("agent_traitant_id")
        .annotate(total=Count("id"))
    )
    charge_rdv = dict(
        RendezVous.objects.filter(statut__in=[RendezVous.DEMANDE, RendezVous.CONFIRME])
        .values_list("agent_traitant_id")
        .annotate(total=Count("id"))
    )

    roles = []
    for info in DESCRIPTION_ROLES:
        comptes = utilisateurs_par_role.get(info["code"], [])
        for compte in comptes:
            compte.nb_dossiers_en_cours = charge_dossiers.get(compte.pk, 0)
            compte.nb_rdv_en_cours = charge_rdv.get(compte.pk, 0)
        roles.append({
            **info,
            "comptes": comptes,
            "nb_comptes": len(comptes),
            "nb_actifs": sum(1 for u in comptes if u.is_active),
        })

    return render(request, "appcadastre/apercu_roles.html", {"roles": roles})

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import administrateur_requis
from .forms import CreationUtilisateurForm, ModifierRoleForm
from .models import Profil


class ConnexionView(auth_views.LoginView):
    template_name = "appcadastre/connexion.html"
    redirect_authenticated_user = True


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
            utilisateur.is_active = form.cleaned_data["actif"]
            utilisateur.is_staff = profil.role == Profil.ADMINISTRATEUR
            utilisateur.is_superuser = profil.role == Profil.ADMINISTRATEUR
            utilisateur.save()
            profil.save()
            messages.success(request, f"Le compte « {utilisateur.username} » a été mis à jour.")
            return redirect("appcadastre:liste_utilisateurs")
    else:
        form = ModifierRoleForm(initial={"role": profil.role, "actif": utilisateur.is_active})

    return render(request, "appcadastre/modifier_utilisateur.html", {
        "form": form, "utilisateur_cible": utilisateur,
    })

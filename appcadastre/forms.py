from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profil


class CreationUtilisateurForm(UserCreationForm):
    """Formulaire utilisé par un administrateur pour créer un compte agent ou administrateur."""

    email = forms.EmailField(required=False, label="Adresse e-mail")
    role = forms.ChoiceField(choices=Profil.ROLE_CHOICES, initial=Profil.AGENT, label="Rôle")
    service = forms.CharField(required=False, label="Service", max_length=100)
    telephone = forms.CharField(required=False, label="Téléphone", max_length=20)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def save(self, commit=True):
        utilisateur = super().save(commit=commit)
        if commit:
            self._appliquer_profil(utilisateur)
        return utilisateur

    def _appliquer_profil(self, utilisateur):
        role = self.cleaned_data["role"]
        profil, _ = Profil.objects.get_or_create(utilisateur=utilisateur)
        profil.role = role
        profil.service = self.cleaned_data.get("service", "")
        profil.telephone = self.cleaned_data.get("telephone", "")
        profil.utilisateur.is_staff = role in (Profil.ADMINISTRATEUR,)
        profil.utilisateur.is_superuser = role == Profil.ADMINISTRATEUR
        profil.utilisateur.save()
        profil.save()


class ModifierRoleForm(forms.Form):
    role = forms.ChoiceField(choices=Profil.ROLE_CHOICES, label="Rôle")
    actif = forms.BooleanField(required=False, label="Compte actif")

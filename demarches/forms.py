from django import forms
from django.contrib.auth.models import User
from django.utils import timezone

from cadastre.models import Commune, Parcelle
from appcadastre.models import Profil

from .models import Dossier, RendezVous


def agents_disponibles():
    """Comptes actifs pouvant se voir attribuer un dossier ou un rendez-vous
    (agents et administrateurs), triés par identifiant."""
    return User.objects.filter(
        is_active=True, profil__role__in=[Profil.AGENT, Profil.ADMINISTRATEUR],
    ).order_by("username")


class DossierForm(forms.ModelForm):
    """Formulaire public de dépôt d'un dossier.

    Le type de dossier n'est plus un champ du formulaire : il est choisi sur
    l'écran précédent (choix de la rubrique puis du type précis) et transmis
    au formulaire via l'argument type_dossier. Selon ce type, le formulaire
    demande soit une parcelle déjà enregistrée (cas de toutes les démarches
    portant sur un bien existant), soit une simple localisation (cas de
    l'immatriculation d'une parcelle qui n'existe pas encore dans le système).
    """

    class Meta:
        model = Dossier
        fields = [
            "parcelle", "localisation_saisie",
            "nom_demandeur", "telephone_demandeur", "email_demandeur", "description",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, type_dossier=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.type_dossier = type_dossier
        self.fields["email_demandeur"].required = False

        if type_dossier == Dossier.IMMATRICULATION:
            # La parcelle n'existe pas encore : seule la localisation a du sens.
            del self.fields["parcelle"]
            self.fields["localisation_saisie"].label = "Localisation du terrain à immatriculer"
            self.fields["localisation_saisie"].required = True
            self.fields["localisation_saisie"].help_text = "Ex. commune et quartier."
        else:
            # Toutes les autres démarches portent sur une parcelle déjà enregistrée.
            del self.fields["localisation_saisie"]
            self.fields["parcelle"].label = "Parcelle concernée"
            self.fields["parcelle"].required = True
            self.fields["parcelle"].queryset = self.fields["parcelle"].queryset.order_by("reference")
            self.fields["parcelle"].empty_label = "— Sélectionner la parcelle concernée —"

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.type_dossier = self.type_dossier
        if commit:
            instance.save()
        return instance


class SuiviForm(forms.Form):
    reference_suivi = forms.CharField(
        label="Référence de suivi", max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "Ex. DOS-2026-8F3K2Q"}),
    )


class TraitementDossierForm(forms.ModelForm):
    """Formulaire administrateur : changement de statut, commentaire de suivi
    et agent responsable du dossier."""

    agent_traitant = forms.ModelChoiceField(
        queryset=User.objects.none(), required=False, label="Agent assigné",
        help_text="Laisser vide pour vous attribuer automatiquement le dossier en l'enregistrant.",
    )

    class Meta:
        model = Dossier
        fields = ["statut", "commentaire_agent", "agent_traitant"]
        widgets = {
            "commentaire_agent": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["agent_traitant"].queryset = agents_disponibles()


class CreerParcelleForm(forms.Form):
    """Formulaire administrateur : création de la vraie parcelle lors de la
    validation d'une demande d'immatriculation."""

    commune = forms.ModelChoiceField(queryset=Commune.objects.all(), label="Commune")
    quartier = forms.CharField(max_length=120, required=False, label="Quartier")
    superficie_m2 = forms.DecimalField(
        max_digits=10, decimal_places=2, label="Superficie (m²)",
    )
    valeur_venale_fcfa = forms.DecimalField(
        max_digits=14, decimal_places=2, label="Valeur vénale estimée (FCFA)",
    )
    usage = forms.ChoiceField(choices=Parcelle.USAGE_CHOICES, label="Usage")


class RechercheEspaceForm(forms.Form):
    """Formulaire public de recherche par téléphone (« Mon espace »)."""
    telephone = forms.CharField(
        label="Numéro de téléphone utilisé lors du dépôt", max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "Ex. 77 123 45 67"}),
    )


class RendezVousForm(forms.ModelForm):
    """Formulaire public de demande de rendez-vous."""

    class Meta:
        model = RendezVous
        fields = [
            "motif", "precision", "date_souhaitee", "creneau",
            "nom_demandeur", "telephone_demandeur", "email_demandeur",
        ]
        widgets = {
            "date_souhaitee": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email_demandeur"].required = False
        self.fields["precision"].widget.attrs["placeholder"] = "Ex. référence de la parcelle ou du dossier"

    def clean_date_souhaitee(self):
        date_souhaitee = self.cleaned_data["date_souhaitee"]
        if date_souhaitee < timezone.now().date():
            raise forms.ValidationError("La date souhaitée ne peut pas être dans le passé.")
        if date_souhaitee.weekday() >= 5:
            raise forms.ValidationError(
                "Les centres des services fiscaux sont fermés le week-end : choisissez un jour de semaine."
            )
        return date_souhaitee


class TraitementRendezVousForm(forms.ModelForm):
    """Formulaire agent : confirmation/annulation d'un rendez-vous et agent responsable."""

    agent_traitant = forms.ModelChoiceField(
        queryset=User.objects.none(), required=False, label="Agent assigné",
        help_text="Laisser vide pour vous attribuer automatiquement le rendez-vous en l'enregistrant.",
    )

    class Meta:
        model = RendezVous
        fields = ["statut", "commentaire_agent", "agent_traitant"]
        widgets = {
            "commentaire_agent": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["agent_traitant"].queryset = agents_disponibles()

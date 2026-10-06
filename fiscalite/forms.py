from django import forms
from django.utils import timezone

from .models import Paiement, TaxeFonciere


class EmettreTaxeForm(forms.Form):
    """Formulaire agent : émission d'un nouvel avis de taxe foncière pour une
    parcelle et une année données. Le taux et le montant ne sont pas saisis à
    la main : ils sont calculés automatiquement à partir de l'usage et de la
    valeur vénale réelle de la parcelle (voir TAUX_PAR_USAGE), pour éviter
    toute incohérence avec le reste de la plateforme."""

    annee = forms.IntegerField(
        label="Année d'imposition", min_value=2000, max_value=2100,
        initial=timezone.now().year,
    )

    def __init__(self, *args, parcelle=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parcelle = parcelle

    def clean_annee(self):
        annee = self.cleaned_data["annee"]
        if self.parcelle and TaxeFonciere.objects.filter(parcelle=self.parcelle, annee=annee).exists():
            raise forms.ValidationError(
                f"Un avis de taxe existe déjà pour l'année {annee} sur cette parcelle."
            )
        return annee


class PaiementForm(forms.ModelForm):
    """Formulaire agent : enregistrement d'un paiement reçu au guichet
    (espèces, mobile money, virement, chèque) pour une taxe foncière
    existante. Le montant ne peut jamais dépasser le solde restant dû."""

    class Meta:
        model = Paiement
        fields = ["montant", "mode_paiement", "reference_transaction"]
        widgets = {
            "reference_transaction": forms.TextInput(attrs={"placeholder": "Facultatif"}),
        }

    def __init__(self, *args, taxe=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.taxe = taxe
        if taxe is not None:
            self.fields["montant"].initial = taxe.solde_restant
            self.fields["montant"].help_text = f"Solde restant dû : {taxe.solde_restant} FCFA."

    def clean_montant(self):
        montant = self.cleaned_data["montant"]
        if montant <= 0:
            raise forms.ValidationError("Le montant doit être supérieur à 0.")
        if self.taxe is not None and montant > self.taxe.solde_restant:
            raise forms.ValidationError(
                f"Ce montant dépasse le solde restant dû ({self.taxe.solde_restant} FCFA)."
            )
        return montant

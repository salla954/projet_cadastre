from django import forms

from .models import Parcelle


class MiseAJourParcelleForm(forms.ModelForm):
    """Formulaire de mise à jour rapide des informations attributaires d'une
    parcelle, utilisé depuis le volet "Analyse spatiale" de la carte
    interactive — pour éviter à l'agent de repasser par QGIS pour une
    simple correction d'attribut."""

    class Meta:
        model = Parcelle
        fields = ["quartier", "usage", "statut", "superficie_m2", "valeur_venale_fcfa"]

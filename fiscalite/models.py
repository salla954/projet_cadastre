import random
import string
from decimal import Decimal
from django.db import models
from django.utils import timezone

from cadastre.models import Parcelle

# Taux de taxe foncière appliqué à la valeur vénale de la parcelle (par usage).
TAUX_PAR_USAGE = {
    "RESIDENTIEL": Decimal("0.05"),
    "COMMERCIAL": Decimal("0.08"),
    "AGRICOLE": Decimal("0.02"),
    "INDUSTRIEL": Decimal("0.07"),
    "MIXTE": Decimal("0.06"),
}

# Prix indicatif au m² (FCFA) utilisé pour estimer la valeur vénale d'une
# parcelle fictive, par usage. Source unique utilisée à la fois par le
# peuplement des données de démonstration et par le simulateur public de
# taxe foncière, pour que les deux restent toujours cohérents entre eux.
PRIX_M2_PAR_USAGE = {
    "RESIDENTIEL": Decimal("25000"),
    "COMMERCIAL": Decimal("55000"),
    "AGRICOLE": Decimal("4000"),
    "INDUSTRIEL": Decimal("35000"),
    "MIXTE": Decimal("30000"),
}


class TaxeFonciere(models.Model):
    """Avis de taxe foncière émis pour une parcelle, pour une année donnée."""

    STATUT_CHOICES = [
        ("EMISE", "Émise"),
        ("PARTIELLEMENT_PAYEE", "Partiellement payée"),
        ("PAYEE", "Payée"),
        ("EN_RETARD", "En retard"),
    ]

    parcelle = models.ForeignKey(
        Parcelle, on_delete=models.CASCADE, related_name="taxes"
    )
    annee = models.PositiveIntegerField(default=timezone.now().year)
    taux_applique = models.DecimalField(max_digits=5, decimal_places=4)
    montant_du = models.DecimalField("Montant dû (FCFA)", max_digits=14, decimal_places=2)
    date_emission = models.DateField(auto_now_add=True)
    date_limite = models.DateField()
    statut = models.CharField(max_length=25, choices=STATUT_CHOICES, default="EMISE")

    class Meta:
        verbose_name = "Taxe foncière"
        verbose_name_plural = "Taxes foncières"
        ordering = ["-annee", "-date_emission"]
        unique_together = [("parcelle", "annee")]

    def __str__(self):
        return f"Taxe {self.annee} — {self.parcelle.reference}"

    @property
    def montant_paye(self):
        total = self.paiements.aggregate(total=models.Sum("montant"))["total"]
        return total or Decimal("0")

    @property
    def solde_restant(self):
        return self.montant_du - self.montant_paye


def _generer_reference_quittance():
    """Génère une référence de quittance lisible, ex. QUIT-2026-8F3K2Q."""
    suffixe = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"QUIT-{timezone.now().year}-{suffixe}"


class Paiement(models.Model):
    """Paiement effectué en règlement (total ou partiel) d'une taxe foncière."""

    MODE_CHOICES = [
        ("ESPECES", "Espèces"),
        ("MOBILE_MONEY", "Mobile Money"),
        ("VIREMENT", "Virement bancaire"),
        ("CHEQUE", "Chèque"),
    ]

    taxe = models.ForeignKey(
        TaxeFonciere, on_delete=models.CASCADE, related_name="paiements"
    )
    reference_quittance = models.CharField(
        "Référence de quittance", max_length=20, unique=True, editable=False, blank=True,
    )
    montant = models.DecimalField(max_digits=14, decimal_places=2)
    mode_paiement = models.CharField(max_length=20, choices=MODE_CHOICES, default="ESPECES")
    date_paiement = models.DateField(auto_now_add=True)
    reference_transaction = models.CharField(max_length=60, blank=True)

    def save(self, *args, **kwargs):
        if not self.reference_quittance:
            reference = _generer_reference_quittance()
            while Paiement.objects.filter(reference_quittance=reference).exists():
                reference = _generer_reference_quittance()
            self.reference_quittance = reference
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ["-date_paiement"]

    def __str__(self):
        return f"Paiement {self.montant} FCFA — {self.taxe}"

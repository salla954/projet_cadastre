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
    montant = models.DecimalField(max_digits=14, decimal_places=2)
    mode_paiement = models.CharField(max_length=20, choices=MODE_CHOICES, default="ESPECES")
    date_paiement = models.DateField(auto_now_add=True)
    reference_transaction = models.CharField(max_length=60, blank=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ["-date_paiement"]

    def __str__(self):
        return f"Paiement {self.montant} FCFA — {self.taxe}"

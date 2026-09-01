from django.db import models
from django.urls import reverse


class Commune(models.Model):
    """Commune ou arrondissement de la région de Thiès."""
    nom = models.CharField(max_length=100, unique=True)
    population_estimee = models.PositiveIntegerField(
        "Population estimée", blank=True, null=True
    )

    class Meta:
        verbose_name = "Commune"
        verbose_name_plural = "Communes"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Proprietaire(models.Model):
    """Personne physique ou morale détentrice d'une ou plusieurs parcelles."""

    TYPE_CHOICES = [
        ("PHYSIQUE", "Personne physique"),
        ("MORALE", "Personne morale"),
    ]

    type_proprietaire = models.CharField(
        "Type", max_length=10, choices=TYPE_CHOICES, default="PHYSIQUE"
    )
    nom_complet = models.CharField("Nom complet / Raison sociale", max_length=200)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    nin_ou_rccm = models.CharField(
        "NIN / RCCM", max_length=50, blank=True,
        help_text="Numéro d'identification nationale ou registre de commerce"
    )

    class Meta:
        verbose_name = "Propriétaire"
        verbose_name_plural = "Propriétaires"
        ordering = ["nom_complet"]

    def __str__(self):
        return self.nom_complet


class Parcelle(models.Model):
    """Unité cadastrale de base."""

    STATUT_CHOICES = [
        ("IMMATRICULEE", "Immatriculée"),
        ("EN_COURS", "En cours d'immatriculation"),
        ("LITIGE", "En litige"),
        ("NON_IMMATRICULEE", "Non immatriculée"),
    ]

    USAGE_CHOICES = [
        ("RESIDENTIEL", "Résidentiel"),
        ("COMMERCIAL", "Commercial"),
        ("AGRICOLE", "Agricole"),
        ("INDUSTRIEL", "Industriel"),
        ("MIXTE", "Mixte"),
    ]

    reference = models.CharField(
        "Référence cadastrale", max_length=30, unique=True,
        help_text="Ex : TH-2024-00147"
    )
    commune = models.ForeignKey(
        Commune, on_delete=models.PROTECT, related_name="parcelles"
    )
    proprietaire = models.ForeignKey(
        Proprietaire, on_delete=models.PROTECT, related_name="parcelles"
    )
    quartier = models.CharField(max_length=120, blank=True)
    superficie_m2 = models.DecimalField(
        "Superficie (m²)", max_digits=10, decimal_places=2
    )
    valeur_venale_fcfa = models.DecimalField(
        "Valeur vénale estimée (FCFA)", max_digits=14, decimal_places=2
    )
    usage = models.CharField(max_length=20, choices=USAGE_CHOICES, default="RESIDENTIEL")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="NON_IMMATRICULEE")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    date_creation = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Parcelle"
        verbose_name_plural = "Parcelles"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.reference} — {self.commune}"

    def get_absolute_url(self):
        return reverse("cadastre:parcelle_detail", args=[self.pk])


class PointBornage(models.Model):
    """Sommet du contour réel d'une parcelle, dans un repère local en mètres.

    Saisis dans l'ordre du contour (sens horaire ou antihoraire, peu importe
    tant que c'est cohérent), ces points permettent de tracer le vrai polygone
    de la parcelle sur l'extrait de plan, au lieu d'un simple rectangle
    proportionné à la superficie. Le repère est libre (ce n'est pas forcément
    du GPS/UTM) : seule l'échelle relative entre les points compte.
    """

    parcelle = models.ForeignKey(
        Parcelle, on_delete=models.CASCADE, related_name="points_bornage"
    )
    ordre = models.PositiveSmallIntegerField(
        "Ordre",
        help_text="Position du point dans le contour (1, 2, 3…), à la suite les uns des autres."
    )
    label = models.CharField(
        "Repère de la borne", max_length=10, blank=True,
        help_text="Ex : B1, B2… (laisser vide pour un numérotage automatique)"
    )
    x = models.DecimalField("X (m)", max_digits=10, decimal_places=2)
    y = models.DecimalField("Y (m)", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Point de bornage"
        verbose_name_plural = "Points de bornage"
        ordering = ["parcelle", "ordre"]
        constraints = [
            models.UniqueConstraint(
                fields=["parcelle", "ordre"], name="unique_ordre_par_parcelle"
            )
        ]

    def __str__(self):
        return f"{self.label or f'Point {self.ordre}'} — {self.parcelle.reference}"

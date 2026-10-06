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
    contour_carte = models.JSONField(
        "Contour réel (WGS84) pour la carte interactive", blank=True, null=True,
        help_text=(
            "Liste de points [latitude, longitude] du contour extérieur réel de la "
            "parcelle, en coordonnées géographiques (WGS84), utilisée pour dessiner "
            "un vrai polygone sur la carte interactive plutôt qu'un simple point. "
            "Renseigné uniquement pour les parcelles importées depuis une géométrie "
            "réelle (voir la commande importer_bd_zone_nguinth) ; laisser vide pour "
            "les parcelles fictives, qui restent affichées par un point."
        ),
    )
    date_creation = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Parcelle"
        verbose_name_plural = "Parcelles"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.reference} — {self.commune}"

    def get_absolute_url(self):
        return reverse("cadastre:parcelle_detail", args=[self.pk])

    @property
    def decoupage_nicad(self):
        """Décompose la référence en ses six composantes officielles si elle
        suit le format du NICAD (16 chiffres) défini par l'article 3 du
        décret n° 2012-396 du 27 mars 2012 : RR DD AA CC SSS PPPPP.

        - RR (2) : région
        - DD (2) : département
        - AA (2) : arrondissement
        - CC (2) : commune, commune d'arrondissement ou communauté rurale
        - SSS (3) : section cadastrale
        - PPPPP (5) : numéro de la parcelle dans cette section

        Renvoie None si la référence ne suit pas ce format (les références
        fictives type "TH-2024-00147" des données de démonstration, ou un
        simple numéro de lot) : cette décomposition ne s'applique qu'aux
        parcelles dotées d'un vrai NICAD, comme celles importées depuis la
        zone de Nguinth.
        """
        ref = self.reference
        if not (len(ref) == 16 and ref.isdigit()):
            return None
        return {
            "region": ref[0:2],
            "departement": ref[2:4],
            "arrondissement": ref[4:6],
            "commune": ref[6:8],
            "section_cadastrale": ref[8:11],
            "numero_parcelle": ref[11:16],
        }


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


class ExtraitPlanGenere(models.Model):
    """Trace chaque génération d'un extrait de plan cadastral (PDF).

    Ne stocke pas le fichier lui-même (généré à la volée à chaque demande),
    seulement l'événement, afin de permettre un suivi statistique du nombre
    d'extraits délivrés (voir le tableau de bord)."""

    parcelle = models.ForeignKey(
        Parcelle, on_delete=models.CASCADE, related_name="extraits_generes"
    )
    date_generation = models.DateTimeField("Date de génération", auto_now_add=True)

    class Meta:
        verbose_name = "Extrait de plan généré"
        verbose_name_plural = "Extraits de plan générés"
        ordering = ["-date_generation"]

    def __str__(self):
        return f"Extrait {self.parcelle.reference} — {self.date_generation:%d/%m/%Y %H:%M}"

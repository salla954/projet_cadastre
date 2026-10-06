from django.conf import settings
from django.db import models


class Profil(models.Model):
    """
    Profil étendant l'utilisateur Django avec un rôle métier.

    Trois profils existent dans l'application :
    - VISITEUR  : grand public, aucune authentification requise (accès aux
                  pages publiques : accueil, actualités, consultation d'une
                  parcelle par référence, à propos).
    - AGENT     : agent du cadastre / des impôts, authentifié, accès au
                  back-office (tableau de bord, gestion des parcelles et
                  des taxes) mais pas à la gestion des comptes.
    - ADMINISTRATEUR : authentifié, accès complet au back-office ainsi qu'à
                  la gestion des comptes utilisateurs et à l'admin Django.
    """

    ADMINISTRATEUR = "ADMINISTRATEUR"
    AGENT = "AGENT"
    VISITEUR = "VISITEUR"

    ROLE_CHOICES = [
        (ADMINISTRATEUR, "Administrateur"),
        (AGENT, "Agent"),
        (VISITEUR, "Visiteur"),
    ]

    # Spécialité / mission confiée à un agent — n'a de sens que pour les rôles
    # AGENT et ADMINISTRATEUR. Sert à orienter l'attribution des dossiers et
    # rendez-vous vers l'agent le plus pertinent.
    GENERALISTE = "GENERALISTE"
    SPECIALITE_CADASTRE = "CADASTRE"
    SPECIALITE_FISCALITE = "FISCALITE"
    SPECIALITE_ACCUEIL = "ACCUEIL"
    SPECIALITE_CHOICES = [
        (GENERALISTE, "Généraliste"),
        (SPECIALITE_CADASTRE, "Cadastre"),
        (SPECIALITE_FISCALITE, "Fiscalité"),
        (SPECIALITE_ACCUEIL, "Accueil & rendez-vous"),
    ]

    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profil",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=AGENT)
    specialite = models.CharField(
        "Spécialité / mission", max_length=20, choices=SPECIALITE_CHOICES,
        default=GENERALISTE, blank=True,
        help_text="Domaine principal de responsabilité de cet agent (facultatif, pour orienter l'attribution des dossiers).",
    )
    communes_attribuees = models.ManyToManyField(
        "cadastre.Commune", verbose_name="Communes attribuées", blank=True,
        related_name="agents_attribues",
        help_text="Communes dont cet agent a la charge. Laisser vide pour toutes les communes.",
    )
    telephone = models.CharField(max_length=20, blank=True)
    service = models.CharField(
        max_length=100, blank=True,
        help_text="Ex : Service du Cadastre, Service des Impôts...",
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"

    def __str__(self):
        return f"{self.utilisateur.get_username()} ({self.get_role_display()})"

    @property
    def est_administrateur(self):
        return self.role == self.ADMINISTRATEUR or self.utilisateur.is_superuser

    @property
    def est_agent(self):
        return self.role in (self.AGENT, self.ADMINISTRATEUR) or self.utilisateur.is_superuser

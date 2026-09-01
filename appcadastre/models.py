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

    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profil",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=AGENT)
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

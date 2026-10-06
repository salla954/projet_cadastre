import random
import string

from django.conf import settings
from django.db import models
from django.utils import timezone

from cadastre.models import Parcelle


def generer_reference_suivi():
    """Génère une référence de suivi lisible, ex. DOS-2026-8F3K2Q."""
    suffixe = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"DOS-{timezone.now().year}-{suffixe}"


def generer_reference_rdv():
    """Génère une référence de rendez-vous lisible, ex. RDV-2026-8F3K2Q."""
    suffixe = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"RDV-{timezone.now().year}-{suffixe}"


class Dossier(models.Model):
    """Un dossier déposé par un usager : une demande relevant du cadastre ou
    de la fiscalité foncière.

    Suivi par une référence publique (reference_suivi), sans nécessiter de compte
    utilisateur côté demandeur. Le traitement (changement de statut, commentaire)
    est réservé aux agents connectés.
    """

    FAMILLE_CADASTRE = "Cadastre"
    FAMILLE_FISCALITE = "Fiscalité"
    FAMILLE_CHOICES = [
        (FAMILLE_CADASTRE, "Cadastre"),
        (FAMILLE_FISCALITE, "Fiscalité"),
    ]

    # --- Cadastre ---
    IMMATRICULATION = "IMMATRICULATION"
    PLAN_SITUATION = "PLAN_SITUATION"
    EXTRAIT_CADASTRAL = "EXTRAIT_CADASTRAL"
    RENSEIGNEMENT_PARCELLE = "RENSEIGNEMENT_PARCELLE"
    BORNAGE = "BORNAGE"
    MORCELLEMENT = "MORCELLEMENT"
    FUSION = "FUSION"
    MISE_A_JOUR_CADASTRALE = "MISE_A_JOUR_CADASTRALE"

    # --- Fiscalité ---
    SITUATION_FISCALE = "SITUATION_FISCALE"
    ATTESTATION_FISCALE = "ATTESTATION_FISCALE"
    PAIEMENT_QUITTANCE = "PAIEMENT_QUITTANCE"
    REGULARISATION_FISCALE = "REGULARISATION_FISCALE"
    RECLAMATION_FISCALE = "RECLAMATION_FISCALE"
    CONSULTATION_IMPOTS_DUS = "CONSULTATION_IMPOTS_DUS"

    # Choix groupés par rubrique : Django affiche automatiquement ces groupes
    # comme des <optgroup> dans les formulaires (dépôt, filtres agent), et
    # get_type_dossier_display() fonctionne normalement avec cette structure.
    TYPE_CHOICES = [
        (FAMILLE_CADASTRE, [
            (IMMATRICULATION, "Immatriculation d'une parcelle"),
            (PLAN_SITUATION, "Plan de situation"),
            (EXTRAIT_CADASTRAL, "Extrait cadastral"),
            (RENSEIGNEMENT_PARCELLE, "Renseignements sur une parcelle"),
            (BORNAGE, "Bornage"),
            (MORCELLEMENT, "Morcellement"),
            (FUSION, "Fusion"),
            (MISE_A_JOUR_CADASTRALE, "Mise à jour cadastrale"),
        ]),
        (FAMILLE_FISCALITE, [
            (SITUATION_FISCALE, "Situation fiscale"),
            (ATTESTATION_FISCALE, "Attestation fiscale"),
            (PAIEMENT_QUITTANCE, "Paiement / quittance"),
            (REGULARISATION_FISCALE, "Régularisation fiscale"),
            (RECLAMATION_FISCALE, "Réclamation"),
            (CONSULTATION_IMPOTS_DUS, "Consultation des impôts dus"),
        ]),
    ]

    # Table de correspondance type -> rubrique, construite une fois pour toutes
    # à partir de TYPE_CHOICES (une seule source de vérité, jamais désynchronisée).
    FAMILLE_PAR_TYPE = {
        valeur: nom_famille
        for nom_famille, options in TYPE_CHOICES
        for valeur, _ in options
    }

    DEPOSE = "DEPOSE"
    EN_COURS = "EN_COURS"
    VALIDE = "VALIDE"
    REJETE = "REJETE"
    STATUT_CHOICES = [
        (DEPOSE, "Déposé"),
        (EN_COURS, "En cours d'instruction"),
        (VALIDE, "Validé"),
        (REJETE, "Rejeté"),
    ]

    reference_suivi = models.CharField(
        "Référence de suivi", max_length=20, unique=True, editable=False,
    )
    type_dossier = models.CharField("Type de dossier", max_length=30, choices=TYPE_CHOICES)
    parcelle = models.ForeignKey(
        Parcelle, verbose_name="Parcelle concernée", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="dossiers",
        help_text="À renseigner si la parcelle est déjà enregistrée (ex. pour une réclamation).",
    )
    localisation_saisie = models.CharField(
        "Localisation (si parcelle non encore enregistrée)", max_length=255, blank=True,
        help_text="Ex. commune et quartier — utile pour une demande d'immatriculation d'une parcelle qui n'existe pas encore dans le système.",
    )
    nom_demandeur = models.CharField("Nom complet du demandeur", max_length=150)
    telephone_demandeur = models.CharField("Téléphone", max_length=20)
    email_demandeur = models.EmailField("E-mail", blank=True)
    description = models.TextField("Description de la demande ou de la réclamation")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default=DEPOSE)
    commentaire_agent = models.TextField(
        "Commentaire de l'agent (visible par le demandeur lors du suivi)", blank=True,
    )
    agent_traitant = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Agent traitant", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="dossiers_traites",
    )
    date_depot = models.DateTimeField("Date de dépôt", auto_now_add=True)
    date_maj = models.DateTimeField("Dernière mise à jour", auto_now=True)

    class Meta:
        verbose_name = "Dossier"
        verbose_name_plural = "Dossiers"
        ordering = ["-date_depot"]

    def save(self, *args, **kwargs):
        if not self.reference_suivi:
            reference = generer_reference_suivi()
            while Dossier.objects.filter(reference_suivi=reference).exists():
                reference = generer_reference_suivi()
            self.reference_suivi = reference
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference_suivi} — {self.get_type_dossier_display()}"

    @property
    def famille(self):
        """Rubrique du dossier ("Cadastre" ou "Fiscalité"), déduite de son type."""
        return self.FAMILLE_PAR_TYPE.get(self.type_dossier, "")


class PieceJointe(models.Model):
    """Un document déposé à l'appui d'un dossier (pièce d'identité, plan, etc.)."""

    dossier = models.ForeignKey(Dossier, on_delete=models.CASCADE, related_name="pieces_jointes")
    fichier = models.FileField("Fichier", upload_to="dossiers/%Y/%m/")
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pièce jointe"
        verbose_name_plural = "Pièces jointes"

    def __str__(self):
        return self.nom_fichier

    @property
    def nom_fichier(self):
        return self.fichier.name.rsplit("/", 1)[-1]


class RendezVous(models.Model):
    """Une demande de rendez-vous avec un agent (bornage, remise de document,
    contestation…), à confirmer par un agent. Suivi par une référence
    publique, sans compte utilisateur côté demandeur — même logique que Dossier.
    """

    MOTIF_CHOICES = [
        ("BORNAGE", "Bornage sur le terrain"),
        ("RETRAIT_DOCUMENT", "Retrait d'un document"),
        ("CONTESTATION", "Contestation ou réclamation"),
        ("CONSEIL", "Conseil sur une démarche"),
        ("AUTRE", "Autre motif"),
    ]

    CRENEAU_CHOICES = [
        ("MATIN", "Matin (8h00 – 13h30)"),
        ("APRES_MIDI", "Après-midi (14h30 – 17h00)"),
    ]

    DEMANDE = "DEMANDE"
    CONFIRME = "CONFIRME"
    ANNULE = "ANNULE"
    HONORE = "HONORE"
    STATUT_CHOICES = [
        (DEMANDE, "Demandé"),
        (CONFIRME, "Confirmé"),
        (ANNULE, "Annulé"),
        (HONORE, "Honoré"),
    ]

    reference_suivi = models.CharField(
        "Référence de suivi", max_length=20, unique=True, editable=False,
    )
    motif = models.CharField(max_length=20, choices=MOTIF_CHOICES)
    precision = models.CharField(
        "Précision (facultatif)", max_length=255, blank=True,
        help_text="Ex. référence de la parcelle ou du dossier concerné.",
    )
    date_souhaitee = models.DateField("Date souhaitée")
    creneau = models.CharField(max_length=15, choices=CRENEAU_CHOICES)
    nom_demandeur = models.CharField("Nom complet", max_length=150)
    telephone_demandeur = models.CharField("Téléphone", max_length=20)
    email_demandeur = models.EmailField("E-mail", blank=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default=DEMANDE)
    commentaire_agent = models.TextField(
        "Commentaire de l'agent (visible par le demandeur lors du suivi)", blank=True,
    )
    agent_traitant = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Agent traitant", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="rendez_vous_traites",
    )
    date_creation = models.DateTimeField("Date de la demande", auto_now_add=True)
    date_maj = models.DateTimeField("Dernière mise à jour", auto_now=True)

    class Meta:
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"
        ordering = ["date_souhaitee", "creneau"]

    def save(self, *args, **kwargs):
        if not self.reference_suivi:
            reference = generer_reference_rdv()
            while RendezVous.objects.filter(reference_suivi=reference).exists():
                reference = generer_reference_rdv()
            self.reference_suivi = reference
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference_suivi} — {self.get_motif_display()} le {self.date_souhaitee}"

from django.conf import settings
from django.db import models
from django.utils import timezone


class Actualite(models.Model):
    """Article d'information publié sur le site public (actualités, guides, avis)."""
    titre = models.CharField(max_length=200)
    chapo = models.CharField("Chapô (résumé court)", max_length=300)
    contenu = models.TextField()
    date_publication = models.DateTimeField("Date de publication", default=timezone.now)
    publie = models.BooleanField(default=True)
    source_url = models.URLField(
        "Lien vers la source officielle", max_length=300, blank=True,
        help_text="Ex. lien vers l'article original sur dgid.sn, pour permettre au lecteur de vérifier l'information.",
    )

    class Meta:
        verbose_name = "Actualité"
        verbose_name_plural = "Actualités"
        ordering = ["-date_publication"]

    def __str__(self):
        return self.titre


class SectionGuide(models.Model):
    """Section du contenu du guide du visiteur, gérée librement par les agents
    (ajout, modification, suppression, réorganisation) sans intervention sur le code."""

    CATEGORIE_COMPRENDRE = "COMPRENDRE"
    CATEGORIE_IMMATRICULER = "IMMATRICULER"
    CATEGORIE_FISCALITE = "FISCALITE"
    CATEGORIE_PRATIQUE = "PRATIQUE"
    CATEGORIE_CHOICES = [
        (CATEGORIE_COMPRENDRE, "Comprendre le cadastre"),
        (CATEGORIE_IMMATRICULER, "Immatriculer une parcelle"),
        (CATEGORIE_FISCALITE, "Fiscalité foncière"),
        (CATEGORIE_PRATIQUE, "Pratique"),
    ]

    titre = models.CharField(max_length=200)
    contenu = models.TextField(
        help_text="Texte de la section. Les sauts de ligne sont conservés à l'affichage.",
    )
    categorie = models.CharField(
        "Rubrique", max_length=20, choices=CATEGORIE_CHOICES, default=CATEGORIE_COMPRENDRE,
        help_text="Thème sous lequel la section est regroupée sur la page publique du guide.",
    )
    ordre = models.PositiveIntegerField(
        "Ordre d'affichage", default=0,
        help_text="Les sections sont affichées de la plus petite à la plus grande valeur.",
    )
    publie = models.BooleanField(default=True)
    date_maj = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Section du guide"
        verbose_name_plural = "Sections du guide"
        ordering = ["ordre", "id"]

    def __str__(self):
        return self.titre


class Notification(models.Model):
    """Message généré automatiquement à chaque évolution d'un dossier ou d'un
    rendez-vous (dépôt, changement de statut), pour informer l'usager de
    l'avancement de sa démarche. Consultable sans compte, via une recherche
    par téléphone — même logique que « Mon espace » — depuis l'onglet
    « Mes notifications ».

    Référence le dossier/rendez-vous via une chaîne ('demarches.Dossier') afin
    d'éviter toute dépendance directe de core vers l'app demarches à l'import :
    seul demarches importe core (JournalActivite), jamais l'inverse.
    """

    dossier = models.ForeignKey(
        "demarches.Dossier", verbose_name="Dossier concerné", on_delete=models.CASCADE,
        null=True, blank=True, related_name="notifications",
    )
    rendez_vous = models.ForeignKey(
        "demarches.RendezVous", verbose_name="Rendez-vous concerné", on_delete=models.CASCADE,
        null=True, blank=True, related_name="notifications",
    )
    telephone_destinataire = models.CharField(
        "Téléphone du destinataire", max_length=20,
        help_text="Copié depuis le dossier/rendez-vous au moment de la création.",
    )
    message = models.CharField("Message", max_length=255)
    date_creation = models.DateTimeField("Date", auto_now_add=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-date_creation"]

    def __str__(self):
        return self.message

    @property
    def reference_suivi(self):
        if self.dossier_id:
            return self.dossier.reference_suivi
        if self.rendez_vous_id:
            return self.rendez_vous.reference_suivi
        return ""

    @classmethod
    def creer(cls, *, dossier=None, rendez_vous=None, message):
        """Raccourci pour ajouter une notification depuis une vue, sans jamais
        faire échouer l'action principale si la notification elle-même
        posait problème (même philosophie que JournalActivite.enregistrer)."""
        telephone = ""
        if dossier is not None:
            telephone = dossier.telephone_demandeur
        elif rendez_vous is not None:
            telephone = rendez_vous.telephone_demandeur
        try:
            cls.objects.create(
                dossier=dossier, rendez_vous=rendez_vous,
                telephone_destinataire=telephone, message=message,
            )
        except Exception:
            pass


class JournalActivite(models.Model):
    """Trace les actions importantes effectuées par les agents (émission de
    taxe, paiement enregistré, dossier traité, rendez-vous confirmé…), pour
    la traçabilité et la responsabilisation — consultable par un
    administrateur uniquement."""

    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Agent", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="actions_journal",
    )
    action = models.CharField("Action", max_length=255)
    details = models.TextField("Détails", blank=True)
    date_action = models.DateTimeField("Date", auto_now_add=True)

    class Meta:
        verbose_name = "Entrée du journal d'activité"
        verbose_name_plural = "Journal d'activité"
        ordering = ["-date_action"]

    def __str__(self):
        return f"{self.action} — {self.date_action:%d/%m/%Y %H:%M}"

    @classmethod
    def enregistrer(cls, agent, action, details=""):
        """Raccourci pour ajouter une entrée au journal depuis n'importe
        quelle vue, sans jamais faire échouer l'action principale si la
        journalisation elle-même posait problème."""
        try:
            cls.objects.create(agent=agent if getattr(agent, "is_authenticated", False) else None,
                                action=action, details=details)
        except Exception:
            pass

import random
import re

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from appcadastre.decorators import agent_requis, peut_acceder_rubrique
from appcadastre.models import Profil
from cadastre.models import Parcelle, Proprietaire
from core.models import JournalActivite, Notification
from core.utils import generer_recu_pdf, reponse_csv

from .forms import (
    CreerParcelleForm, DossierForm, RechercheEspaceForm, RendezVousForm,
    SuiviForm, TraitementDossierForm, TraitementRendezVousForm, agents_disponibles,
)
from .models import Dossier, PieceJointe, RendezVous

# Pièces jointes : on limite volontairement taille et types acceptés, pour
# éviter qu'un usager ne dépose des fichiers trop lourds ou inadaptés.
TAILLE_MAX_FICHIER = 10 * 1024 * 1024  # 10 Mo
EXTENSIONS_AUTORISEES = (".pdf", ".jpg", ".jpeg", ".png")

# Libellés de tous les types valides, aplatis depuis TYPE_CHOICES (groupé par
# rubrique) — pour valider un type reçu dans l'URL et l'afficher facilement.
LIBELLES_TYPE = {
    valeur: libelle
    for _, options in Dossier.TYPE_CHOICES
    for valeur, libelle in options
}

# Aide contextuelle affichée au-dessus de la description, adaptée à chaque
# type de demande — pour que chaque formulaire guide vraiment l'usager sur
# ce qu'il doit préciser, plutôt qu'un même texte générique pour tous les types.
AIDE_PAR_TYPE = {
    Dossier.IMMATRICULATION: "Décrivez le terrain (usage envisagé, mise en valeur actuelle) et joignez tout document utile (plan, attestation de mise en valeur).",
    Dossier.PLAN_SITUATION: "Précisez l'usage prévu du plan de situation (vente, prêt bancaire, construction…).",
    Dossier.EXTRAIT_CADASTRAL: "Indiquez pour quel usage l'extrait cadastral est demandé.",
    Dossier.RENSEIGNEMENT_PARCELLE: "Précisez les informations recherchées (statut, propriétaire, superficie…).",
    Dossier.BORNAGE: "Décrivez les limites contestées ou à faire préciser sur le terrain.",
    Dossier.MORCELLEMENT: "Indiquez le nombre de lots souhaités et leur destination.",
    Dossier.FUSION: "Précisez les références des autres parcelles à fusionner avec celle sélectionnée.",
    Dossier.MISE_A_JOUR_CADASTRALE: "Décrivez le changement à prendre en compte (construction, démolition, changement d'usage…).",
    Dossier.SITUATION_FISCALE: "Précisez la période concernée par la situation fiscale demandée.",
    Dossier.ATTESTATION_FISCALE: "Indiquez l'usage prévu de l'attestation (marché public, banque, notaire…).",
    Dossier.PAIEMENT_QUITTANCE: "Précisez l'année et, si possible, le montant du paiement concerné.",
    Dossier.REGULARISATION_FISCALE: "Décrivez votre situation et l'échéancier de paiement souhaité.",
    Dossier.RECLAMATION_FISCALE: "Décrivez précisément l'erreur constatée sur votre avis de taxe foncière.",
    Dossier.CONSULTATION_IMPOTS_DUS: "Précisez la période pour laquelle vous souhaitez connaître les impôts dus.",
}

# Documents généralement utiles pour chaque type de demande, affichés au-dessus
# du champ de dépôt de fichiers. Rien n'est bloquant si l'usager ne les a pas
# sous la main (le champ reste facultatif), mais l'indication "recommandé"
# l'invite fortement à les joindre pour accélérer le traitement.
# Documents attendus pour chaque type de demande, affichés au-dessus du champ
# de dépôt de fichiers. Au moins un fichier est désormais obligatoire pour
# déposer un dossier, quel que soit le type (voir la validation dans la vue).
DOCUMENTS_PAR_TYPE = {
    Dossier.IMMATRICULATION: [
        "Pièce d'identité", "Justificatif de propriété ou d'occupation",
        "Plan de bornage (si disponible)", "Photos du terrain",
    ],
    Dossier.PLAN_SITUATION: ["Pièce d'identité"],
    Dossier.EXTRAIT_CADASTRAL: ["Pièce d'identité"],
    Dossier.RENSEIGNEMENT_PARCELLE: ["Pièce d'identité"],
    Dossier.BORNAGE: [
        "Titre foncier ou justificatif de propriété", "Ancien plan de bornage (si disponible)",
    ],
    Dossier.MORCELLEMENT: [
        "Titre foncier", "Plan de division proposé (nombre et disposition des lots)",
    ],
    Dossier.FUSION: [
        "Titres fonciers des parcelles à fusionner",
    ],
    Dossier.MISE_A_JOUR_CADASTRALE: [
        "Justificatif du changement (permis de construire, certificat de conformité…)",
    ],
    Dossier.SITUATION_FISCALE: ["Pièce d'identité"],
    Dossier.ATTESTATION_FISCALE: ["Pièce d'identité"],
    Dossier.PAIEMENT_QUITTANCE: ["Ancienne quittance ou avis de taxe (si disponible)"],
    Dossier.REGULARISATION_FISCALE: ["Avis de taxe concernés (si disponibles)"],
    Dossier.RECLAMATION_FISCALE: ["Avis de taxe contesté"],
    Dossier.CONSULTATION_IMPOTS_DUS: ["Pièce d'identité"],
}


def choisir_type_dossier(request):
    """Première étape du dépôt : l'usager choisit la rubrique puis le type
    précis de sa demande, avant d'accéder au formulaire correspondant."""
    return render(request, "demarches/choisir_type.html", {
        "type_choices": Dossier.TYPE_CHOICES,
    })


def assistant_demarche(request):
    """Questionnaire guidé (2 à 4 questions) qui oriente l'usager vers le bon
    type de démarche parmi les 14 disponibles, plutôt que de les lui montrer
    tous d'un coup — alternative à l'écran de choix classique pour qui ne
    sait pas encore précisément ce qu'il lui faut."""
    tous_les_types = [
        (valeur, libelle) for _, options in Dossier.TYPE_CHOICES for valeur, libelle in options
    ]
    return render(request, "demarches/assistant.html", {"tous_les_types": tous_les_types})


def deposer_dossier(request, type_dossier):
    libelle_type = LIBELLES_TYPE.get(type_dossier)
    if libelle_type is None:
        raise Http404("Type de demande inconnu.")

    if request.method == "POST":
        form = DossierForm(request.POST, type_dossier=type_dossier)
        fichiers = request.FILES.getlist("pieces_jointes")
        erreur_fichier = None
        if not fichiers:
            erreur_fichier = "Joignez au moins un document pour déposer votre dossier."
        else:
            for fichier in fichiers:
                if fichier.size > TAILLE_MAX_FICHIER:
                    erreur_fichier = f"« {fichier.name} » dépasse la taille maximale autorisée (10 Mo)."
                    break
                if not fichier.name.lower().endswith(EXTENSIONS_AUTORISEES):
                    erreur_fichier = f"« {fichier.name} » : format non accepté (PDF, JPG ou PNG uniquement)."
                    break

        if form.is_valid() and not erreur_fichier:
            dossier = form.save()
            for fichier in fichiers:
                PieceJointe.objects.create(dossier=dossier, fichier=fichier)
            Notification.creer(
                dossier=dossier,
                message=f"Votre dossier {dossier.reference_suivi} ({libelle_type}) a bien été déposé et sera examiné par nos services.",
            )
            return redirect("demarches:confirmation", reference=dossier.reference_suivi)
    else:
        form = DossierForm(type_dossier=type_dossier)
        erreur_fichier = None

    documents_suggeres = DOCUMENTS_PAR_TYPE.get(type_dossier, [])

    return render(request, "demarches/deposer.html", {
        "form": form,
        "erreur_fichier": erreur_fichier,
        "type_dossier": type_dossier,
        "libelle_type": libelle_type,
        "famille": Dossier.FAMILLE_PAR_TYPE.get(type_dossier),
        "aide_type": AIDE_PAR_TYPE.get(type_dossier, ""),
        "documents_suggeres": documents_suggeres,
    })


def confirmation_depot(request, reference):
    dossier = get_object_or_404(Dossier, reference_suivi=reference)
    return render(request, "demarches/confirmation.html", {"dossier": dossier})


def recu_dossier_pdf(request, reference):
    """Reçu PDF confirmant le dépôt d'un dossier — accessible sans connexion,
    comme le suivi, puisque c'est le demandeur lui-même qui le télécharge."""
    dossier = get_object_or_404(Dossier, reference_suivi=reference)
    lignes = [
        ("Type de démarche", dossier.get_type_dossier_display()),
        ("Rubrique", dossier.famille),
        ("Demandeur", dossier.nom_demandeur),
        ("Téléphone", dossier.telephone_demandeur),
        ("Déposé le", dossier.date_depot.strftime("%d/%m/%Y à %H:%M")),
        ("Statut actuel", dossier.get_statut_display()),
    ]
    if dossier.parcelle:
        lignes.insert(2, ("Parcelle concernée", dossier.parcelle.reference))
    elif dossier.localisation_saisie:
        lignes.insert(2, ("Localisation", dossier.localisation_saisie))
    return generer_recu_pdf(
        "Reçu de dépôt", "Dossier — Cadastre & Fiscalité foncière",
        dossier.reference_suivi, lignes, f"recu-{dossier.reference_suivi}.pdf",
    )


def suivre_dossier(request):
    dossier = None
    erreur = None
    if request.method == "POST":
        form = SuiviForm(request.POST)
        if form.is_valid():
            reference = form.cleaned_data["reference_suivi"].strip().upper()
            try:
                dossier = Dossier.objects.prefetch_related("pieces_jointes").get(
                    reference_suivi=reference
                )
            except Dossier.DoesNotExist:
                erreur = "Aucun dossier ne correspond à cette référence. Vérifiez la saisie."
    else:
        form = SuiviForm()

    return render(request, "demarches/suivre.html", {
        "form": form, "dossier": dossier, "erreur": erreur,
    })


def generer_reference_parcelle():
    """Génère une référence cadastrale unique pour une parcelle nouvellement
    immatriculée suite à la validation d'un dossier."""
    while True:
        reference = f"TH-{timezone.now().year}-{random.randint(100000, 999999)}"
        if not Parcelle.objects.filter(reference=reference).exists():
            return reference


def _familles_autorisees(user):
    """Rubriques (Cadastre/Fiscalité) auxquelles cet utilisateur a accès en
    liste. None = pas de restriction (administrateur, généraliste, accueil)."""
    if peut_acceder_rubrique(user, Profil.SPECIALITE_CADASTRE) and peut_acceder_rubrique(
        user, Profil.SPECIALITE_FISCALITE
    ):
        return None
    if peut_acceder_rubrique(user, Profil.SPECIALITE_CADASTRE):
        return [Dossier.FAMILLE_CADASTRE]
    return [Dossier.FAMILLE_FISCALITE]


@agent_requis
def liste_dossiers(request):
    dossiers = Dossier.objects.select_related("parcelle", "agent_traitant").all()

    familles_autorisees = _familles_autorisees(request.user)
    famille_choices = Dossier.FAMILLE_CHOICES
    if familles_autorisees is not None:
        types_autorises = [
            valeur for nom, options in Dossier.TYPE_CHOICES
            if nom in familles_autorisees for valeur, _ in options
        ]
        dossiers = dossiers.filter(type_dossier__in=types_autorises)
        famille_choices = [c for c in Dossier.FAMILLE_CHOICES if c[0] in familles_autorisees]

    statut = request.GET.get("statut", "")
    type_dossier = request.GET.get("type", "")
    famille = request.GET.get("famille", "")
    agent = request.GET.get("agent", "")
    if statut:
        dossiers = dossiers.filter(statut=statut)
    if type_dossier:
        dossiers = dossiers.filter(type_dossier=type_dossier)
    if famille:
        types_de_la_famille = [
            valeur for nom, options in Dossier.TYPE_CHOICES if nom == famille for valeur, _ in options
        ]
        dossiers = dossiers.filter(type_dossier__in=types_de_la_famille)
    if agent == "non_assigne":
        dossiers = dossiers.filter(agent_traitant__isnull=True)
    elif agent:
        dossiers = dossiers.filter(agent_traitant_id=agent)

    if request.GET.get("export") == "csv":
        lignes = [
            [d.reference_suivi, d.get_type_dossier_display(), d.famille, d.nom_demandeur,
             d.telephone_demandeur, d.date_depot.strftime("%d/%m/%Y"), d.get_statut_display()]
            for d in dossiers
        ]
        return reponse_csv(
            "dossiers.csv",
            ["Référence", "Type", "Rubrique", "Demandeur", "Téléphone", "Déposé le", "Statut"],
            lignes,
        )

    return render(request, "demarches/agent_liste.html", {
        "dossiers": dossiers,
        "statut_choices": Dossier.STATUT_CHOICES,
        "type_choices": Dossier.TYPE_CHOICES,
        "famille_choices": famille_choices,
        "agents_choices": agents_disponibles(),
        "agent_selectionne": agent,
        "statut_selectionne": statut,
        "type_selectionne": type_dossier,
        "famille_selectionnee": famille,
    })


@agent_requis
def detail_dossier(request, pk):
    dossier = get_object_or_404(
        Dossier.objects.prefetch_related("pieces_jointes"), pk=pk
    )
    specialite_associee = (
        Profil.SPECIALITE_CADASTRE if dossier.famille == Dossier.FAMILLE_CADASTRE
        else Profil.SPECIALITE_FISCALITE
    )
    if not peut_acceder_rubrique(request.user, specialite_associee):
        raise PermissionDenied(
            "Ce dossier relève de la rubrique "
            f"« {dossier.famille} », qui n'est pas celle de votre spécialité."
        )
    ancien_statut = dossier.statut
    form = TraitementDossierForm(instance=dossier)
    form_parcelle = CreerParcelleForm()

    peut_creer_parcelle = dossier.type_dossier == Dossier.IMMATRICULATION and not dossier.parcelle

    if request.method == "POST" and request.POST.get("action") == "creer_parcelle":
        form_parcelle = CreerParcelleForm(request.POST)
        if peut_creer_parcelle and form_parcelle.is_valid():
            proprietaire, _ = Proprietaire.objects.get_or_create(
                nom_complet=dossier.nom_demandeur,
                defaults={
                    "telephone": dossier.telephone_demandeur,
                    "email": dossier.email_demandeur,
                },
            )
            parcelle = Parcelle.objects.create(
                reference=generer_reference_parcelle(),
                commune=form_parcelle.cleaned_data["commune"],
                proprietaire=proprietaire,
                quartier=form_parcelle.cleaned_data.get("quartier") or dossier.localisation_saisie,
                superficie_m2=form_parcelle.cleaned_data["superficie_m2"],
                valeur_venale_fcfa=form_parcelle.cleaned_data["valeur_venale_fcfa"],
                usage=form_parcelle.cleaned_data["usage"],
                statut="IMMATRICULEE",
            )
            dossier.parcelle = parcelle
            dossier.statut = Dossier.VALIDE
            dossier.agent_traitant = request.user
            if not dossier.commentaire_agent:
                dossier.commentaire_agent = (
                    f"Votre parcelle a été immatriculée sous la référence {parcelle.reference}. "
                    "Vous pouvez la consulter via « Consulter une parcelle »."
                )
            dossier.save()
            JournalActivite.enregistrer(
                request.user, "Parcelle créée depuis un dossier d'immatriculation",
                f"Dossier {dossier.reference_suivi} → parcelle {parcelle.reference}",
            )
            if ancien_statut != dossier.statut:
                Notification.creer(
                    dossier=dossier,
                    message=f"Votre dossier {dossier.reference_suivi} est maintenant « {dossier.get_statut_display()} ». {dossier.commentaire_agent}".strip(),
                )
            messages.success(
                request,
                f"Parcelle {parcelle.reference} créée et liée au dossier. Communiquez cette "
                "référence à l'agent chargé du dossier si nécessaire.",
            )
            return redirect("demarches:detail_dossier", pk=dossier.pk)

    elif request.method == "POST":
        form = TraitementDossierForm(request.POST, instance=dossier)
        if form.is_valid():
            dossier = form.save(commit=False)
            if not dossier.agent_traitant:
                dossier.agent_traitant = request.user
            dossier.save()
            JournalActivite.enregistrer(
                request.user, f"Dossier {dossier.get_statut_display().lower()}",
                f"Dossier {dossier.reference_suivi} ({dossier.get_type_dossier_display()}) — "
                f"assigné à {dossier.agent_traitant.get_username() if dossier.agent_traitant else 'personne'}",
            )
            if ancien_statut != dossier.statut:
                message_notif = f"Votre dossier {dossier.reference_suivi} est maintenant « {dossier.get_statut_display()} »."
                if dossier.commentaire_agent:
                    message_notif += f" {dossier.commentaire_agent}"
                Notification.creer(dossier=dossier, message=message_notif)
            messages.success(request, "Dossier mis à jour avec succès.")
            return redirect("demarches:detail_dossier", pk=dossier.pk)

    return render(request, "demarches/agent_detail.html", {
        "dossier": dossier,
        "form": form,
        "form_parcelle": form_parcelle,
        "peut_creer_parcelle": peut_creer_parcelle,
    })


def _normaliser_telephone(numero):
    """Ne garde que les chiffres d'un numéro de téléphone, pour comparer deux
    numéros saisis avec une mise en forme différente (espaces, indicatif +221...)."""
    return re.sub(r"\D", "", numero or "")


def prendre_rdv(request):
    if request.method == "POST":
        form = RendezVousForm(request.POST)
        if form.is_valid():
            rdv = form.save()
            Notification.creer(
                rendez_vous=rdv,
                message=f"Votre demande de rendez-vous {rdv.reference_suivi} ({rdv.get_motif_display()}) a bien été enregistrée.",
            )
            return redirect("demarches:confirmation_rdv", reference=rdv.reference_suivi)
    else:
        form = RendezVousForm()
    return render(request, "demarches/prendre_rdv.html", {"form": form})


def confirmation_rdv(request, reference):
    rdv = get_object_or_404(RendezVous, reference_suivi=reference)
    return render(request, "demarches/confirmation_rdv.html", {"rdv": rdv})


def recu_rdv_pdf(request, reference):
    """Reçu PDF confirmant une demande de rendez-vous — accessible sans
    connexion, comme le suivi, puisque c'est le demandeur qui le télécharge."""
    rdv = get_object_or_404(RendezVous, reference_suivi=reference)
    lignes = [
        ("Motif", rdv.get_motif_display()),
        ("Date souhaitée", rdv.date_souhaitee.strftime("%d/%m/%Y")),
        ("Créneau", rdv.get_creneau_display()),
        ("Demandeur", rdv.nom_demandeur),
        ("Téléphone", rdv.telephone_demandeur),
        ("Statut actuel", rdv.get_statut_display()),
    ]
    if rdv.precision:
        lignes.insert(1, ("Précision", rdv.precision))
    return generer_recu_pdf(
        "Reçu de demande", "Rendez-vous — Cadastre & Fiscalité foncière",
        rdv.reference_suivi, lignes, f"recu-{rdv.reference_suivi}.pdf",
    )


def mon_espace(request):
    """Recherche tous les dossiers ET rendez-vous liés à un numéro de
    téléphone — contrairement au suivi par référence (qui ne montre qu'un
    dossier à la fois), utile pour un usager qui a plusieurs démarches en
    cours. Recherche insensible à la mise en forme du numéro (espaces,
    indicatif +221...), sans nécessiter de compte.
    """
    dossiers = None
    rendez_vous = None
    recherche_effectuee = False

    if request.method == "POST":
        form = RechercheEspaceForm(request.POST)
        if form.is_valid():
            recherche_effectuee = True
            numero_normalise = _normaliser_telephone(form.cleaned_data["telephone"])
            dossiers = [
                d for d in Dossier.objects.select_related("parcelle").all()
                if numero_normalise and numero_normalise in _normaliser_telephone(d.telephone_demandeur)
            ]
            rendez_vous = [
                r for r in RendezVous.objects.all()
                if numero_normalise and numero_normalise in _normaliser_telephone(r.telephone_demandeur)
            ]
    else:
        form = RechercheEspaceForm()

    return render(request, "demarches/mon_espace.html", {
        "form": form,
        "dossiers": dossiers,
        "rendez_vous": rendez_vous,
        "recherche_effectuee": recherche_effectuee,
    })


def mes_notifications(request):
    """Historique chronologique des notifications (dépôt, changements de statut)
    pour toutes les démarches liées à un numéro de téléphone — même principe
    de recherche que « Mon espace », sans nécessiter de compte."""
    notifications = None
    recherche_effectuee = False

    if request.method == "POST":
        form = RechercheEspaceForm(request.POST)
        if form.is_valid():
            recherche_effectuee = True
            numero_normalise = _normaliser_telephone(form.cleaned_data["telephone"])
            notifications = [
                n for n in Notification.objects.select_related(
                    "dossier", "rendez_vous"
                ).all()
                if numero_normalise and numero_normalise in _normaliser_telephone(n.telephone_destinataire)
            ]
    else:
        form = RechercheEspaceForm()

    return render(request, "demarches/mes_notifications.html", {
        "form": form,
        "notifications": notifications,
        "recherche_effectuee": recherche_effectuee,
    })


@agent_requis
def liste_rdv(request):
    rendez_vous = RendezVous.objects.select_related("agent_traitant").all()
    statut = request.GET.get("statut", "")
    agent = request.GET.get("agent", "")
    if statut:
        rendez_vous = rendez_vous.filter(statut=statut)
    if agent == "non_assigne":
        rendez_vous = rendez_vous.filter(agent_traitant__isnull=True)
    elif agent:
        rendez_vous = rendez_vous.filter(agent_traitant_id=agent)
    return render(request, "demarches/agent_liste_rdv.html", {
        "rendez_vous": rendez_vous,
        "statut_choices": RendezVous.STATUT_CHOICES,
        "statut_selectionne": statut,
        "agents_choices": agents_disponibles(),
        "agent_selectionne": agent,
    })


@agent_requis
def detail_rdv(request, pk):
    rdv = get_object_or_404(RendezVous, pk=pk)
    ancien_statut = rdv.statut
    if request.method == "POST":
        form = TraitementRendezVousForm(request.POST, instance=rdv)
        if form.is_valid():
            rdv = form.save(commit=False)
            if not rdv.agent_traitant:
                rdv.agent_traitant = request.user
            rdv.save()
            JournalActivite.enregistrer(
                request.user, f"Rendez-vous {rdv.get_statut_display().lower()}",
                f"Rendez-vous {rdv.reference_suivi} ({rdv.get_motif_display()}) — "
                f"assigné à {rdv.agent_traitant.get_username() if rdv.agent_traitant else 'personne'}",
            )
            if ancien_statut != rdv.statut:
                message_notif = f"Votre rendez-vous {rdv.reference_suivi} est maintenant « {rdv.get_statut_display()} »."
                if rdv.commentaire_agent:
                    message_notif += f" {rdv.commentaire_agent}"
                Notification.creer(rendez_vous=rdv, message=message_notif)
            messages.success(request, "Rendez-vous mis à jour.")
            return redirect("demarches:detail_rdv", pk=rdv.pk)
    else:
        form = TraitementRendezVousForm(instance=rdv)
    return render(request, "demarches/agent_detail_rdv.html", {"rdv": rdv, "form": form})

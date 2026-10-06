from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator

from appcadastre.decorators import fiscalite_agent_requis
from cadastre.models import Parcelle
from core.models import JournalActivite
from core.utils import reponse_csv, generer_recu_pdf
from .forms import EmettreTaxeForm, PaiementForm
from .models import TaxeFonciere, Paiement, TAUX_PAR_USAGE


@fiscalite_agent_requis
def liste_taxes(request):
    taxes = TaxeFonciere.objects.select_related("parcelle", "parcelle__commune").all()

    statut = request.GET.get("statut")
    annee = request.GET.get("annee")
    if statut:
        taxes = taxes.filter(statut=statut)
    if annee:
        taxes = taxes.filter(annee=annee)

    if request.GET.get("export") == "csv":
        lignes = [
            [t.parcelle.reference, t.annee, t.montant_du, t.montant_paye,
             t.solde_restant, t.get_statut_display()]
            for t in taxes
        ]
        return reponse_csv(
            "taxes_foncieres.csv",
            ["Parcelle", "Année", "Montant dû (FCFA)", "Montant payé (FCFA)", "Solde (FCFA)", "Statut"],
            lignes,
        )

    paginator = Paginator(taxes, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    annees = TaxeFonciere.objects.values_list("annee", flat=True).distinct().order_by("-annee")

    return render(request, "fiscalite/liste_taxes.html", {
        "page_obj": page_obj,
        "statut_choices": TaxeFonciere.STATUT_CHOICES,
        "annees": annees,
        "filtres": {"statut": statut, "annee": annee},
    })


@fiscalite_agent_requis
def detail_taxe(request, pk):
    taxe = get_object_or_404(
        TaxeFonciere.objects.select_related("parcelle").prefetch_related("paiements"),
        pk=pk,
    )
    return render(request, "fiscalite/detail_taxe.html", {"taxe": taxe})


@fiscalite_agent_requis
def emettre_taxe_recherche(request):
    """Point d'entrée visible depuis le tableau de bord et la liste des
    taxes : l'agent recherche une parcelle par sa référence, sans avoir
    besoin d'être déjà sur sa fiche, avant d'émettre un avis de taxe."""
    parcelle = None
    erreur = None
    reference = request.GET.get("reference", "").strip()
    if reference:
        parcelle = Parcelle.objects.filter(reference__iexact=reference).first()
        if parcelle is None:
            erreur = f"Aucune parcelle ne correspond à la référence « {reference} »."
    return render(request, "fiscalite/emettre_taxe_recherche.html", {
        "reference": reference, "parcelle": parcelle, "erreur": erreur,
    })


@fiscalite_agent_requis
def emettre_taxe(request, parcelle_pk):
    """Émet un nouvel avis de taxe foncière pour une parcelle et une année
    choisies par l'agent. Le taux et le montant dû sont calculés
    automatiquement à partir de l'usage et de la valeur vénale réelle de la
    parcelle — jamais saisis à la main, pour rester cohérent avec le reste de
    la plateforme (simulateur public compris)."""
    parcelle = get_object_or_404(Parcelle, pk=parcelle_pk)
    if request.method == "POST":
        form = EmettreTaxeForm(request.POST, parcelle=parcelle)
        if form.is_valid():
            annee = form.cleaned_data["annee"]
            taux = TAUX_PAR_USAGE.get(parcelle.usage, Decimal("0.05"))
            montant_du = (parcelle.valeur_venale_fcfa * taux).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
            taxe = TaxeFonciere.objects.create(
                parcelle=parcelle, annee=annee, taux_applique=taux,
                montant_du=montant_du, date_limite=date(annee, 12, 31), statut="EMISE",
            )
            JournalActivite.enregistrer(
                request.user, "Avis de taxe émis",
                f"Parcelle {parcelle.reference} — année {annee} — {montant_du:,.0f} FCFA".replace(",", " "),
            )
            messages.success(request, f"Avis de taxe {annee} émis pour {montant_du:,.0f} FCFA.".replace(",", " "))
            return redirect("fiscalite:detail_taxe", pk=taxe.pk)
    else:
        form = EmettreTaxeForm(parcelle=parcelle)

    taux_apercu = TAUX_PAR_USAGE.get(parcelle.usage, Decimal("0.05"))
    montant_apercu = (parcelle.valeur_venale_fcfa * taux_apercu).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return render(request, "fiscalite/emettre_taxe.html", {
        "form": form, "parcelle": parcelle,
        "taux_apercu": taux_apercu, "montant_apercu": montant_apercu,
    })


@fiscalite_agent_requis
def enregistrer_paiement_recherche(request):
    """Point d'entrée visible depuis le tableau de bord et la liste des
    taxes : l'agent recherche une parcelle par sa référence, puis choisit
    parmi ses avis de taxe non soldés celui sur lequel enregistrer le
    paiement — sans avoir besoin d'être déjà sur la fiche de cette taxe."""
    parcelle = None
    taxes_impayees = []
    erreur = None
    reference = request.GET.get("reference", "").strip()
    if reference:
        parcelle = Parcelle.objects.filter(reference__iexact=reference).first()
        if parcelle is None:
            erreur = f"Aucune parcelle ne correspond à la référence « {reference} »."
        else:
            taxes_impayees = [
                t for t in TaxeFonciere.objects.filter(parcelle=parcelle).order_by("-annee")
                if t.solde_restant > 0
            ]
    return render(request, "fiscalite/enregistrer_paiement_recherche.html", {
        "reference": reference, "parcelle": parcelle, "erreur": erreur,
        "taxes_impayees": taxes_impayees,
    })


@fiscalite_agent_requis
def enregistrer_paiement(request, taxe_pk):
    """Enregistre un paiement reçu au guichet (espèces, mobile money,
    virement, chèque) pour une taxe foncière existante, et met à jour son
    statut (payée / partiellement payée) en conséquence."""
    taxe = get_object_or_404(TaxeFonciere.objects.select_related("parcelle"), pk=taxe_pk)
    if request.method == "POST":
        form = PaiementForm(request.POST, taxe=taxe)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.taxe = taxe
            paiement.save()
            taxe.statut = "PAYEE" if taxe.solde_restant <= 0 else "PARTIELLEMENT_PAYEE"
            taxe.save(update_fields=["statut"])
            JournalActivite.enregistrer(
                request.user, "Paiement enregistré",
                f"Parcelle {taxe.parcelle.reference} — taxe {taxe.annee} — "
                f"{paiement.montant:,.0f} FCFA ({paiement.get_mode_paiement_display()})".replace(",", " "),
            )
            messages.success(request, "Paiement enregistré.")
            return redirect("fiscalite:detail_taxe", pk=taxe.pk)
    else:
        form = PaiementForm(taxe=taxe)
    return render(request, "fiscalite/enregistrer_paiement.html", {"form": form, "taxe": taxe})


@fiscalite_agent_requis
def quittance_paiement_pdf(request, paiement_pk):
    """Génère la quittance PDF d'un paiement de taxe foncière."""
    paiement = get_object_or_404(
        Paiement.objects.select_related("taxe", "taxe__parcelle", "taxe__parcelle__commune"),
        pk=paiement_pk,
    )
    taxe = paiement.taxe
    lignes = [
        ("Parcelle", taxe.parcelle.reference),
        ("Commune", taxe.parcelle.commune.nom),
        ("Année de la taxe", taxe.annee),
        ("Montant payé", f"{paiement.montant:,.0f} FCFA".replace(",", " ")),
        ("Mode de paiement", paiement.get_mode_paiement_display()),
        ("Date du paiement", paiement.date_paiement.strftime("%d/%m/%Y")),
        ("Solde restant", f"{taxe.solde_restant:,.0f} FCFA".replace(",", " ")),
    ]
    if paiement.reference_transaction:
        lignes.append(("Réf. transaction", paiement.reference_transaction))

    return generer_recu_pdf(
        titre="Quittance de paiement",
        sous_titre="Taxe foncière",
        reference=paiement.reference_quittance,
        lignes=lignes,
        filename=f"quittance_{paiement.reference_quittance}.pdf",
    )
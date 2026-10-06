from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from appcadastre.decorators import cadastre_agent_requis
from core.models import JournalActivite
from core.utils import reponse_csv
from .forms import MiseAJourParcelleForm
from .models import Parcelle, Commune


@cadastre_agent_requis
def liste_parcelles(request):
    """Liste paginée des parcelles avec filtres simples (back-office)."""
    parcelles = Parcelle.objects.select_related("commune", "proprietaire").all()

    commune_id = request.GET.get("commune")
    statut = request.GET.get("statut")
    q = request.GET.get("q", "").strip()

    if commune_id:
        parcelles = parcelles.filter(commune_id=commune_id)
    if statut:
        parcelles = parcelles.filter(statut=statut)
    if q:
        parcelles = parcelles.filter(reference__icontains=q)

    if request.GET.get("export") == "csv":
        lignes = [
            [p.reference, p.commune.nom, str(p.proprietaire), p.get_usage_display(),
             p.get_statut_display(), p.superficie_m2, p.valeur_venale_fcfa]
            for p in parcelles
        ]
        return reponse_csv(
            "parcelles.csv",
            ["Référence", "Commune", "Propriétaire", "Usage", "Statut", "Superficie (m²)", "Valeur vénale (FCFA)"],
            lignes,
        )

    paginator = Paginator(parcelles, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "cadastre/liste_parcelles.html", {
        "page_obj": page_obj,
        "communes": Commune.objects.all(),
        "statut_choices": Parcelle.STATUT_CHOICES,
        "filtres": {"commune": commune_id, "statut": statut, "q": q},
    })


@cadastre_agent_requis
def detail_parcelle(request, pk):
    parcelle = get_object_or_404(
        Parcelle.objects.select_related("commune", "proprietaire"), pk=pk
    )
    return render(request, "cadastre/detail_parcelle.html", {"parcelle": parcelle})


@login_required
@require_GET
def rechercher_parcelle_nicad(request):
    """Recherche d'une parcelle par sa référence (NICAD) depuis la carte."""
    reference = request.GET.get("reference", "").strip()
    if not reference:
        return JsonResponse({"trouvee": False, "erreur": "Saisissez une référence (NICAD)."})

    parcelle = Parcelle.objects.filter(reference__iexact=reference).first()
    if parcelle is None:
        return JsonResponse(
            {"trouvee": False, "erreur": f"Aucune parcelle trouvée pour la référence « {reference} »."}
        )

    if parcelle.latitude is None or parcelle.longitude is None:
        return JsonResponse(
            {"trouvee": False, "erreur": "Cette parcelle existe mais n'est pas géolocalisée sur la carte."}
        )

    return JsonResponse({
        "trouvee": True,
        "pk": parcelle.pk,
        "reference": parcelle.reference,
        "lat": float(parcelle.latitude),
        "lng": float(parcelle.longitude),
        "quartier": parcelle.quartier,
        "usage": parcelle.usage,
        "statut": parcelle.statut,
        "superficie_m2": float(parcelle.superficie_m2),
        "valeur_venale_fcfa": float(parcelle.valeur_venale_fcfa),
    })


@cadastre_agent_requis
@require_POST
def mettre_a_jour_parcelle_carte(request, pk):
    """Met à jour les attributs d'une parcelle depuis la carte (POST en AJAX)."""
    parcelle = get_object_or_404(Parcelle, pk=pk)
    formulaire = MiseAJourParcelleForm(request.POST, instance=parcelle)

    if not formulaire.is_valid():
        return JsonResponse({"succes": False, "erreurs": formulaire.errors}, status=400)

    formulaire.save()
    JournalActivite.enregistrer(
        request.user,
        f"Parcelle {parcelle.reference} mise à jour depuis la carte",
        details=", ".join(formulaire.changed_data),
    )
    return JsonResponse({
        "succes": True,
        "message": f"Parcelle {parcelle.reference} mise à jour.",
    })
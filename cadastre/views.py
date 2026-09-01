from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator

from appcadastre.decorators import agent_requis
from .models import Parcelle, Commune


@agent_requis
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

    paginator = Paginator(parcelles, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "cadastre/liste_parcelles.html", {
        "page_obj": page_obj,
        "communes": Commune.objects.all(),
        "statut_choices": Parcelle.STATUT_CHOICES,
        "filtres": {"commune": commune_id, "statut": statut, "q": q},
    })


@agent_requis
def detail_parcelle(request, pk):
    parcelle = get_object_or_404(
        Parcelle.objects.select_related("commune", "proprietaire"), pk=pk
    )
    return render(request, "cadastre/detail_parcelle.html", {"parcelle": parcelle})

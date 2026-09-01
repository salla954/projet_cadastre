from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator

from appcadastre.decorators import agent_requis
from .models import TaxeFonciere


@agent_requis
def liste_taxes(request):
    taxes = TaxeFonciere.objects.select_related("parcelle", "parcelle__commune").all()

    statut = request.GET.get("statut")
    annee = request.GET.get("annee")
    if statut:
        taxes = taxes.filter(statut=statut)
    if annee:
        taxes = taxes.filter(annee=annee)

    paginator = Paginator(taxes, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    annees = TaxeFonciere.objects.values_list("annee", flat=True).distinct().order_by("-annee")

    return render(request, "fiscalite/liste_taxes.html", {
        "page_obj": page_obj,
        "statut_choices": TaxeFonciere.STATUT_CHOICES,
        "annees": annees,
        "filtres": {"statut": statut, "annee": annee},
    })


@agent_requis
def detail_taxe(request, pk):
    taxe = get_object_or_404(
        TaxeFonciere.objects.select_related("parcelle").prefetch_related("paiements"),
        pk=pk,
    )
    return render(request, "fiscalite/detail_taxe.html", {"taxe": taxe})

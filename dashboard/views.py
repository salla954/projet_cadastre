import json
from django.shortcuts import render
from django.db.models import Sum, Count

from appcadastre.decorators import agent_requis
from cadastre.models import Parcelle, Commune
from fiscalite.models import TaxeFonciere


@agent_requis
def accueil(request):
    # Répartition des parcelles par statut
    par_statut = list(
        Parcelle.objects.values("statut").annotate(total=Count("id")).order_by("-total")
    )

    # Répartition des parcelles par usage
    par_usage = list(
        Parcelle.objects.values("usage").annotate(total=Count("id")).order_by("-total")
    )

    # Taxe due vs. taxe payée par commune (top 8)
    par_commune = (
        Parcelle.objects.values("commune__nom")
        .annotate(nb_parcelles=Count("id"), superficie=Sum("superficie_m2"))
        .order_by("-nb_parcelles")[:8]
    )

    # Recouvrement fiscal par année
    par_annee = list(
        TaxeFonciere.objects.values("annee")
        .annotate(total_du=Sum("montant_du"))
        .order_by("annee")
    )
    # calcul du montant payé par année (somme des paiements liés)
    for ligne in par_annee:
        taxes_annee = TaxeFonciere.objects.filter(annee=ligne["annee"])
        paye = sum(t.montant_paye for t in taxes_annee)
        ligne["total_paye"] = float(paye)
        ligne["total_du"] = float(ligne["total_du"] or 0)

    chiffres = {
        "nb_parcelles": Parcelle.objects.count(),
        "nb_proprietaires": Parcelle.objects.values("proprietaire").distinct().count(),
        "nb_communes": Commune.objects.count(),
        "montant_total_du": TaxeFonciere.objects.aggregate(t=Sum("montant_du"))["t"] or 0,
    }

    contexte = {
        "chiffres": chiffres,
        "par_commune": par_commune,
        "json_statut": json.dumps(list(par_statut)),
        "json_usage": json.dumps(list(par_usage)),
        "json_annee": json.dumps(list(par_annee)),
    }
    return render(request, "dashboard/accueil.html", contexte)

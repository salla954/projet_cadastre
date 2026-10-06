import json
from django.shortcuts import render
from django.db.models import Sum, Count, Avg, F, DurationField, ExpressionWrapper
from django.contrib.auth.models import User

from appcadastre.decorators import agent_requis
from appcadastre.models import Profil
from cadastre.models import Parcelle, Commune, ExtraitPlanGenere
from fiscalite.models import TaxeFonciere
from demarches.models import Dossier, RendezVous


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
    par_commune = list(
        Parcelle.objects.values("commune__nom")
        .annotate(nb_parcelles=Count("id"), superficie=Sum("superficie_m2"))
        .order_by("-nb_parcelles")[:8]
    )
    # Part relative (pour la mini-barre du tableau), calculée par rapport à la
    # commune la plus représentée du top 8.
    maximum_parcelles = max((c["nb_parcelles"] for c in par_commune), default=1) or 1
    for ligne in par_commune:
        ligne["part"] = round(ligne["nb_parcelles"] / maximum_parcelles * 100)

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

    # Répartition des dossiers déposés par statut (immatriculation/réclamation)
    par_statut_dossier = list(
        Dossier.objects.values("statut").annotate(total=Count("id")).order_by("-total")
    )

    # Répartition des dossiers par type précis, groupée par rubrique (Cadastre /
    # Fiscalité). Tous les types apparaissent, même à 0, pour donner une vue
    # complète de chaque nature de demande possible, pas seulement celles déjà
    # utilisées.
    compteurs_par_type = dict(
        Dossier.objects.values_list("type_dossier").annotate(total=Count("id"))
    )
    dossiers_par_famille = {}
    for nom_famille, options in Dossier.TYPE_CHOICES:
        lignes = [
            {"libelle": libelle, "total": compteurs_par_type.get(valeur, 0)}
            for valeur, libelle in options
        ]
        lignes.sort(key=lambda l: -l["total"])
        maximum = max((l["total"] for l in lignes), default=0) or 1
        for ligne in lignes:
            ligne["largeur"] = round(ligne["total"] / maximum * 100)
        dossiers_par_famille[nom_famille] = lignes

    chiffres = {
        "nb_parcelles": Parcelle.objects.count(),
        "nb_proprietaires": Parcelle.objects.values("proprietaire").distinct().count(),
        "nb_communes": Commune.objects.count(),
        "montant_total_du": TaxeFonciere.objects.aggregate(t=Sum("montant_du"))["t"] or 0,
        # NICAD réel : référence à 16 chiffres (format officiel), par opposition
        # aux références fictives (TH-2024-00147...) des données de démonstration.
        "nb_nicad_delivres": Parcelle.objects.filter(reference__regex=r"^\d{16}$").count(),
        "nb_dossiers": Dossier.objects.count(),
        # Approximation du nombre de demandeurs distincts (le dépôt d'un dossier
        # ne nécessite pas de compte utilisateur) : couples nom + téléphone uniques.
        "nb_demandeurs_distincts": Dossier.objects.values(
            "nom_demandeur", "telephone_demandeur"
        ).distinct().count(),
        "nb_extraits_generes": ExtraitPlanGenere.objects.count(),
    }

    contexte = {
        "chiffres": chiffres,
        "par_commune": par_commune,
        "dossiers_par_famille": dossiers_par_famille,
        "json_statut": json.dumps(list(par_statut)),
        "json_usage": json.dumps(list(par_usage)),
        "json_annee": json.dumps(list(par_annee)),
        "json_statut_dossier": json.dumps(par_statut_dossier),
    }
    return render(request, "dashboard/accueil.html", contexte)


@agent_requis
def statistiques_agents(request):
    """Charge de travail et délais moyens de traitement, par agent — pour
    repérer d'un coup d'œil qui est surchargé et où sont les dossiers ou
    rendez-vous en souffrance."""
    agents = (
        User.objects.filter(
            is_active=True, profil__role__in=[Profil.AGENT, Profil.ADMINISTRATEUR],
        )
        .select_related("profil")
        .order_by("username")
    )

    duree_dossier = ExpressionWrapper(
        F("date_maj") - F("date_depot"), output_field=DurationField(),
    )
    duree_rdv = ExpressionWrapper(
        F("date_maj") - F("date_creation"), output_field=DurationField(),
    )

    lignes = []
    for agent in agents:
        dossiers_agent = Dossier.objects.filter(agent_traitant=agent)
        rdv_agent = RendezVous.objects.filter(agent_traitant=agent)

        dossiers_traites = dossiers_agent.filter(statut__in=[Dossier.VALIDE, Dossier.REJETE])
        rdv_traites = rdv_agent.filter(statut__in=[RendezVous.HONORE, RendezVous.ANNULE])

        delai_dossier = dossiers_traites.annotate(duree=duree_dossier).aggregate(m=Avg("duree"))["m"]
        delai_rdv = rdv_traites.annotate(duree=duree_rdv).aggregate(m=Avg("duree"))["m"]

        lignes.append({
            "agent": agent,
            "specialite": agent.profil.get_specialite_display() if hasattr(agent, "profil") else "—",
            "nb_dossiers_en_cours": dossiers_agent.filter(
                statut__in=[Dossier.DEPOSE, Dossier.EN_COURS]
            ).count(),
            "nb_rdv_en_cours": rdv_agent.filter(
                statut__in=[RendezVous.DEMANDE, RendezVous.CONFIRME]
            ).count(),
            "nb_dossiers_traites": dossiers_traites.count(),
            "delai_moyen_dossier_jours": round(delai_dossier.total_seconds() / 86400, 1) if delai_dossier else None,
            "nb_rdv_traites": rdv_traites.count(),
            "delai_moyen_rdv_jours": round(delai_rdv.total_seconds() / 86400, 1) if delai_rdv else None,
        })

    # Les plus chargés en premier : c'est l'information la plus actionnable
    # pour un administrateur qui doit rééquilibrer le travail.
    lignes.sort(key=lambda l: -(l["nb_dossiers_en_cours"] + l["nb_rdv_en_cours"]))

    non_assignes = {
        "dossiers": Dossier.objects.filter(
            agent_traitant__isnull=True, statut__in=[Dossier.DEPOSE, Dossier.EN_COURS],
        ).count(),
        "rendez_vous": RendezVous.objects.filter(
            agent_traitant__isnull=True, statut__in=[RendezVous.DEMANDE, RendezVous.CONFIRME],
        ).count(),
    }

    return render(request, "dashboard/statistiques_agents.html", {
        "lignes": lignes,
        "non_assignes": non_assignes,
    })

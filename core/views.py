from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.http import FileResponse, JsonResponse
from django.urls import reverse
import io
import json
import math
import random
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from appcadastre.decorators import agent_requis, administrateur_requis
from cadastre.models import Parcelle, Commune, ExtraitPlanGenere
from fiscalite.models import TaxeFonciere, TAUX_PAR_USAGE, PRIX_M2_PAR_USAGE
from .forms import ActualiteForm, SectionGuideForm
from .models import Actualite, SectionGuide, JournalActivite


def accueil(request):
    """Page d'accueil publique : chiffres clés + dernières actualités."""
    chiffres = {
        "nb_parcelles": Parcelle.objects.count(),
        "nb_communes": Commune.objects.count(),
        "superficie_totale": Parcelle.objects.aggregate(
            total=Sum("superficie_m2")
        )["total"] or 0,
        "recouvrement_total": TaxeFonciere.objects.aggregate(
            total=Sum("montant_du")
        )["total"] or 0,
    }
    actualites = Actualite.objects.filter(publie=True)[:3]
    return render(request, "core/accueil.html", {
        "chiffres": chiffres,
        "actualites": actualites,
    })


def guide_cadastre(request):
    """Page pédagogique publique : cadastre, immatriculation, valeur vénale et taxe foncière.

    Le contenu est composé de sections gérées librement par les agents (voir
    gestion_guide et les vues associées) plutôt que codées en dur dans le template.
    Les sections sont regroupées par rubrique et affichées sous forme d'accordéons
    (une seule ouverte par défaut) pour rester lisibles malgré le volume de contenu ;
    les sections "Questions fréquentes" et "Glossaire" bénéficient en plus d'une
    mise en forme dédiée (paires question/réponse, grille de définitions).
    """
    icones_categorie = {
        SectionGuide.CATEGORIE_COMPRENDRE: "🧭",
        SectionGuide.CATEGORIE_IMMATRICULER: "🏛️",
        SectionGuide.CATEGORIE_FISCALITE: "💰",
        SectionGuide.CATEGORIE_PRATIQUE: "✅",
    }

    toutes_les_sections = list(SectionGuide.objects.filter(publie=True).order_by("ordre", "id"))
    for section in toutes_les_sections:
        titre_normalise = section.titre.strip().lower()
        if titre_normalise == "questions fréquentes":
            section.type_affichage = "faq"
            section.faq = _analyser_faq(section.contenu)
        elif titre_normalise == "glossaire":
            section.type_affichage = "glossaire"
            section.glossaire = _analyser_glossaire(section.contenu)
        else:
            section.type_affichage = "texte"

        # Complément visuel dynamique pour deux sections précises : la liste
        # d'étapes de l'immatriculation (chronologie) et les taux réels de la
        # taxe foncière fictive (graphique en barres), tous deux calculés à
        # partir des données réelles du code plutôt que recopiés à la main
        # dans le gabarit, pour ne jamais se désynchroniser des taux réels.
        if section.titre.strip() == "Les étapes de la procédure d'immatriculation":
            section.etapes = _analyser_etapes(section.contenu)
        elif section.titre.strip() == "Comment la taxe foncière est-elle calculée ?":
            section.taux_graphique = _taux_par_usage_pour_graphique()

    groupes = []
    for cle, libelle in SectionGuide.CATEGORIE_CHOICES:
        sections_du_groupe = [s for s in toutes_les_sections if s.categorie == cle]
        if sections_du_groupe:
            groupes.append({
                "cle": cle,
                "libelle": libelle,
                "icone": icones_categorie.get(cle, "📄"),
                "sections": sections_du_groupe,
            })

    return render(request, "core/guide_cadastre.html", {"groupes": groupes})


def _analyser_faq(contenu):
    """Découpe le texte d'une section FAQ (paragraphes "Question ?\\nRéponse…")
    en une liste de tuples (question, réponse)."""
    items = []
    for bloc in contenu.split("\n\n"):
        bloc = bloc.strip()
        if not bloc:
            continue
        question, _, reponse = bloc.partition("\n")
        items.append((question.strip(), reponse.strip()))
    return items


def _analyser_glossaire(contenu):
    """Découpe le texte d'une section Glossaire (lignes "Terme : définition")
    en une liste de tuples (terme, définition)."""
    items = []
    for ligne in contenu.split("\n"):
        ligne = ligne.strip()
        if not ligne:
            continue
        terme, separateur, definition = ligne.partition(" : ")
        if separateur:
            items.append((terme.strip(), definition.strip()))
    return items


def _analyser_etapes(contenu):
    """Extrait le numéro et le titre court de chaque étape numérotée
    ("1. Titre : description…") pour la frise chronologique visuelle ; la
    description complète, elle, reste affichée telle quelle dans le texte de
    la section (liens compris)."""
    etapes = []
    for ligne in contenu.split("\n"):
        ligne = ligne.strip()
        match = re.match(r"^(\d+)\.\s*(.+)$", ligne)
        if not match:
            continue
        numero, reste = match.groups()
        titre, separateur, _ = reste.partition(" : ")
        if separateur:
            etapes.append({"numero": numero, "titre": titre.strip()})
    return etapes


def _taux_par_usage_pour_graphique():
    """Construit les données du graphique en barres des taux de taxe foncière
    (données de démonstration) à partir de TAUX_PAR_USAGE et USAGE_CHOICES :
    une seule source de vérité, partagée avec le calcul réel des taxes."""
    libelles = dict(Parcelle.USAGE_CHOICES)
    valeurs = [
        (libelles.get(cle, cle), float(taux) * 100)
        for cle, taux in TAUX_PAR_USAGE.items()
    ]
    valeurs.sort(key=lambda item: item[1], reverse=True)
    maximum = max((pourcentage for _, pourcentage in valeurs), default=1) or 1
    return [
        {
            "libelle": libelle,
            "pourcentage": pourcentage,
            "largeur": round(pourcentage / maximum * 100),
        }
        for libelle, pourcentage in valeurs
    ]


def liste_actualites(request):
    actualites = Actualite.objects.filter(publie=True)
    return render(request, "core/liste_actualites.html", {"actualites": actualites})


def detail_actualite(request, pk):
    actualite = get_object_or_404(Actualite, pk=pk, publie=True)
    return render(request, "core/detail_actualite.html", {"actualite": actualite})


def consultation_publique(request):
    """Recherche publique d'une parcelle par sa référence cadastrale."""
    resultat = None
    reference = request.GET.get("reference", "").strip()
    if reference:
        resultat = Parcelle.objects.filter(reference__iexact=reference).first()
    return render(request, "core/consultation_publique.html", {
        "resultat": resultat,
        "reference": reference,
    })


@login_required
def carte_parcelles(request):
    """Carte interactive des parcelles géolocalisées (Leaflet) — réservée aux agents connectés."""
    return render(request, "core/carte_parcelles.html", {
        "communes": Commune.objects.all(),
        "statut_choices": Parcelle.STATUT_CHOICES,
        "usage_choices": Parcelle.USAGE_CHOICES,
    })


def _polygones_grille_commune(parcelles_commune, graine_commune):
    """Dispose les parcelles fictives d'une commune sur une grille compacte,
    sans chevauchement, façon mosaïque de blocs cadastraux — bien plus
    réaliste qu'un rectangle indépendant tournant librement autour de chaque
    point (ce qui produisait un enchevêtrement chaotique).

    Le centre de la grille est la position moyenne réelle des parcelles de la
    commune ; chaque parcelle occupe sa propre cellule (jamais partagée), de
    taille modulée selon sa superficie réelle (dans une fourchette limitée
    pour ne pas casser l'alignement de la grille) ; toute la grille est
    tournée d'un angle unique (pas chaque parcelle séparément), pour un effet
    de quartier orienté différemment d'une commune à l'autre sans créer de
    chevauchement interne. Renvoie un dict {parcelle.pk: polygone}.
    """
    alea = random.Random(graine_commune)
    n = len(parcelles_commune)
    if n == 0:
        return {}

    lat_centre = sum(float(p.latitude) for p in parcelles_commune) / n
    lon_centre = sum(float(p.longitude) for p in parcelles_commune) / n

    colonnes = max(1, math.ceil(math.sqrt(n)))
    superficies = [float(p.superficie_m2) for p in parcelles_commune]
    superficie_moyenne = sum(superficies) / n
    # Cellule de base un peu plus grande que la parcelle moyenne, pour
    # ménager une "rue" visible entre les blocs.
    cote_cellule = math.sqrt(superficie_moyenne) * 3.2

    angle_bloc = math.radians(alea.uniform(0, 360))
    cos_b, sin_b = math.cos(angle_bloc), math.sin(angle_bloc)
    metres_par_degre_lat = 111_320
    metres_par_degre_lon = 111_320 * math.cos(math.radians(lat_centre)) or 1

    lignes = math.ceil(n / colonnes)
    largeur_totale = colonnes * cote_cellule
    hauteur_totale = lignes * cote_cellule

    resultat = {}
    for indice, parcelle in enumerate(parcelles_commune):
        ligne, colonne = divmod(indice, colonnes)
        # Centre de la cellule, avant rotation du bloc entier.
        cx = colonne * cote_cellule - largeur_totale / 2 + cote_cellule / 2
        cy = ligne * cote_cellule - hauteur_totale / 2 + cote_cellule / 2

        # Taille de la parcelle dans sa cellule : reflète sa superficie
        # réelle, mais bornée pour ne jamais déborder sur la cellule voisine.
        facteur = (float(parcelle.superficie_m2) / superficie_moyenne) ** 0.5
        facteur = min(1.15, max(0.55, facteur))
        demi_largeur = (cote_cellule * 0.42) * facteur
        demi_hauteur = demi_largeur * alea.uniform(0.75, 1.0)

        coins_locaux = [(-demi_largeur, -demi_hauteur), (demi_largeur, -demi_hauteur),
                        (demi_largeur, demi_hauteur), (-demi_largeur, demi_hauteur)]

        polygone = []
        for x, y in coins_locaux:
            xt, yt = x + cx, y + cy
            xr = xt * cos_b - yt * sin_b
            yr = xt * sin_b + yt * cos_b
            polygone.append([
                lat_centre + yr / metres_par_degre_lat,
                lon_centre + xr / metres_par_degre_lon,
            ])
        resultat[parcelle.pk] = polygone
    return resultat


@login_required
def carte_parcelles_donnees(request):
    """Renvoie en JSON les parcelles géolocalisées, pour affichage sur la carte.

    Vue réservée aux agents connectés : par souci de confidentialité, aucune information sur le
    propriétaire n'est transmise ici (uniquement des données déjà visibles
    via la consultation publique par référence).
    """
    parcelles = list(Parcelle.objects.select_related("commune").filter(
        latitude__isnull=False, longitude__isnull=False
    ))

    commune_id = request.GET.get("commune", "").strip()
    statut = request.GET.get("statut", "").strip()
    usage = request.GET.get("usage", "").strip()
    if commune_id:
        parcelles = [p for p in parcelles if str(p.commune_id) == commune_id]
    if statut:
        parcelles = [p for p in parcelles if p.statut == statut]
    if usage:
        parcelles = [p for p in parcelles if p.usage == usage]

    # Les parcelles sans contour réel connu (données fictives, ou parcelles
    # importées dont la géométrie n'a pas pu être extraite) sont disposées en
    # grille par commune plutôt qu'indépendamment les unes des autres, pour
    # éviter tout chevauchement (voir _polygones_grille_commune) — la carte
    # ne doit jamais réduire une parcelle à un simple point.
    parcelles_sans_contour_par_commune = {}
    for p in parcelles:
        if not p.contour_carte:
            parcelles_sans_contour_par_commune.setdefault(p.commune_id, []).append(p)
    polygones_indicatifs = {}
    for commune_id_groupe, groupe in parcelles_sans_contour_par_commune.items():
        polygones_indicatifs.update(_polygones_grille_commune(groupe, commune_id_groupe))

    donnees = []
    ignorees = 0
    for p in parcelles:
        try:
            url_consultation = f"{reverse('core:consultation_publique')}?reference={p.reference}"
            url_plan = reverse("core:extrait_plan", args=[p.reference])
        except Exception:
            # Certaines références réelles (ex. Nicad contenant un "/") ne sont pas
            # compatibles avec le convertisseur d'URL <str:reference>. On ignore
            # ces parcelles pour l'affichage carte plutôt que de faire planter
            # l'ensemble de la réponse.
            ignorees += 1
            continue
        donnees.append({
            "reference": p.reference,
            "commune": p.commune.nom,
            "quartier": p.quartier or "Non précisé",
            "usage": p.usage,
            "usage_libelle": p.get_usage_display(),
            "statut": p.statut,
            "statut_libelle": p.get_statut_display(),
            "superficie_m2": float(p.superficie_m2),
            "lat": float(p.latitude),
            "lng": float(p.longitude),
            # Contour réel pour les parcelles importées dont la géométrie a pu
            # être extraite ; sinon, un contour indicatif calculé en grille
            # par commune (voir _polygones_grille_commune), pour que la carte
            # n'affiche jamais une parcelle réduite à un simple point.
            "polygone": p.contour_carte or polygones_indicatifs.get(p.pk),
            "est_indicatif": p.contour_carte is None,
            "url_consultation": url_consultation,
            "url_plan": url_plan,
        })

    return JsonResponse({"parcelles": donnees, "total": len(donnees), "ignorees": ignorees})


@agent_requis
def extrait_plan_pdf(request, reference):
    """Génère et télécharge un extrait de plan cadastral (PDF) pour une parcelle.

    Le schéma de la parcelle est un rectangle indicatif proportionné à la
    superficie enregistrée (la plateforme ne stocke pas la géométrie exacte
    issue du bornage) ; ce document est donc à visée pédagogique/démonstrative
    et ne remplace pas un plan de bornage officiel.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader
    import random
    import os

    parcelle = get_object_or_404(Parcelle, reference__iexact=reference)
    ExtraitPlanGenere.objects.create(parcelle=parcelle)

    BLEU_NUIT = HexColor("#1B2A4A")
    OCRE = HexColor("#C98A2C")
    VERT = HexColor("#3A6B4C")
    OR = HexColor("#E4A94F")
    ROUGE = HexColor("#B3452C")
    GRIS = HexColor("#4B5262")
    SABLE = HexColor("#F7F4EE")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largeur_page, hauteur_page = A4
    marge = 20 * mm

    # ---- Cadre général façon document officiel ----
    cadre_marge = 10 * mm
    cadre_bas = 9 * mm
    c.setStrokeColor(BLEU_NUIT)
    c.setLineWidth(1.1)
    c.rect(cadre_marge, cadre_bas, largeur_page - 2 * cadre_marge,
           hauteur_page - cadre_marge - cadre_bas, stroke=1, fill=0)
    c.setLineWidth(0.4)
    c.rect(cadre_marge + 1.6 * mm, cadre_bas + 1.6 * mm,
           largeur_page - 2 * cadre_marge - 3.2 * mm,
           hauteur_page - cadre_marge - cadre_bas - 3.2 * mm, stroke=1, fill=0)

    # ---- Logo DGID, en haut à droite du cadre ----
    chemin_logo = os.path.join(os.path.dirname(__file__), "images.jpg")
    logo_h = 16 * mm
    logo_y = hauteur_page - cadre_marge - 4 * mm - logo_h
    if os.path.exists(chemin_logo):
        try:
            image_logo = ImageReader(chemin_logo)
            largeur_native, hauteur_native = image_logo.getSize()
            logo_l = logo_h * (largeur_native / hauteur_native)
            logo_x = largeur_page - cadre_marge - 6 * mm - logo_l
            c.drawImage(image_logo, logo_x, logo_y, width=logo_l, height=logo_h,
                        preserveAspectRatio=True, mask="auto")
        except Exception:
            pass  # logo manquant ou illisible : le document reste généré sans lui

    y = logo_y - 6 * mm

    # ---- Cartouche institutionnel (3 colonnes, à la manière d'un titre foncier) ----
    zone_largeur = largeur_page - 2 * marge
    col1_w = 48 * mm
    col3_w = 52 * mm
    col2_w = zone_largeur - col1_w - col3_w
    col1_x = marge
    col2_x = marge + col1_w
    col3_x = marge + col1_w + col2_w
    y_cartouche_haut = y

    # -- Colonne 1 : institution --
    cy = y_cartouche_haut
    cx = col1_x + col1_w / 2
    c.setFillColor(BLEU_NUIT)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(cx, cy, "RÉPUBLIQUE DU SÉNÉGAL")
    cy -= 3.6 * mm
    c.setFont("Helvetica-Oblique", 6)
    c.setFillColor(GRIS)
    c.drawCentredString(cx, cy, "Un Peuple – Un But – Une Foi")
    cy -= 5.5 * mm
    c.setFont("Helvetica", 6)
    for ligne in ["Ministère des Finances", "et du Budget", "Direction Générale des Impôts", "et des Domaines"]:
        c.drawCentredString(cx, cy, ligne)
        cy -= 3.2 * mm
    cy -= 1 * mm
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(BLEU_NUIT)
    c.drawCentredString(cx, cy, "BUREAU DU CADASTRE")
    cy -= 3.4 * mm
    c.drawCentredString(cx, cy, "DE THIÈS")
    bas_col1 = cy

    # -- Colonne 2 : titre et localisation --
    cy = y_cartouche_haut
    cx = col2_x + col2_w / 2
    c.setFillColor(BLEU_NUIT)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(cx, cy, "EXTRAIT DE PLAN")
    cy -= 5.5 * mm
    c.drawCentredString(cx, cy, "CADASTRAL")
    cy -= 7 * mm
    c.setFont("Helvetica", 8.5)
    c.setFillColor(GRIS)
    c.drawCentredString(cx, cy, "Région de Thiès")
    cy -= 4.2 * mm
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(BLEU_NUIT)
    c.drawCentredString(cx, cy, f"Commune de {parcelle.commune}")
    cy -= 4.2 * mm
    c.setFont("Helvetica", 8.5)
    c.setFillColor(GRIS)
    c.drawCentredString(cx, cy, f"Quartier {parcelle.quartier}" if parcelle.quartier else "Quartier non précisé")
    cy -= 5 * mm
    c.setFont("Helvetica", 8.5)
    c.setFillColor(GRIS)
    c.drawCentredString(cx, cy, "Requérant")
    cy -= 4.2 * mm
    c.setFont("Helvetica-Bold", 9.5)
    c.setFillColor(BLEU_NUIT)
    c.drawCentredString(cx, cy, str(parcelle.proprietaire))
    bas_col2 = cy

    # -- Colonne 3 : références du dossier --
    cy = y_cartouche_haut
    cx = col3_x
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(BLEU_NUIT)
    c.drawString(cx, cy, "PLATEFORME CADASTRE")
    cy -= 3.4 * mm
    c.setFont("Helvetica", 6)
    c.setFillColor(GRIS)
    c.drawString(cx, cy, "& Fiscalité foncière — Thiès")
    cy -= 6 * mm

    statut_labels = {
        "IMMATRICULEE": "Immatriculée",
        "EN_COURS": "En cours d'immatriculation",
        "LITIGE": "En litige",
        "NON_IMMATRICULEE": "Non immatriculée",
    }
    champs_dossier = [
        ("Réf. cadastrale", parcelle.reference),
        ("Statut", statut_labels.get(parcelle.statut, parcelle.statut)),
        ("Usage", parcelle.get_usage_display()),
        ("Dossier n°", f"{parcelle.pk:06d}"),
        ("Édité le", date.today().strftime("%d/%m/%Y")),
    ]
    for label, valeur in champs_dossier:
        c.setFont("Helvetica", 6.5)
        c.setFillColor(GRIS)
        c.drawString(cx, cy, f"{label} :")
        c.setFont("Helvetica-Bold", 6.5)
        c.setFillColor(BLEU_NUIT)
        c.drawString(cx + 20 * mm, cy, str(valeur))
        cy -= 3.6 * mm
    bas_col3 = cy

    y = min(bas_col1, bas_col2, bas_col3) - 2 * mm

    c.setStrokeColor(BLEU_NUIT)
    c.setLineWidth(0.8)
    c.line(marge, y, largeur_page - marge, y)
    y -= 6 * mm

    # ---- Bandeau "Plan de situation" / NORD / Superficie ----
    points_bornage = list(parcelle.points_bornage.order_by("ordre"))
    mode_polygone = len(points_bornage) >= 3

    bande_situation_h = 48 * mm
    situation_bas = y - bande_situation_h

    # Vignette "Plan de situation" — îlots cadastraux subdivisés en parcelles,
    # séparés par des rues, avec la parcelle principale mise en évidence par un
    # contour épais et son numéro. Motif indicatif, non géoréférencé, en noir et
    # blanc, dans l'esprit d'un plan de situation cadastral administratif.
    vignette_l = 62 * mm
    c.setFillColor(HexColor("#FFFFFF"))
    c.rect(marge, situation_bas, vignette_l, bande_situation_h, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#000000"))
    c.setLineWidth(0.9)
    c.rect(marge, situation_bas, vignette_l, bande_situation_h, stroke=1, fill=0)

    alea_situation = random.Random(parcelle.pk)

    # Petite flèche NORD en haut de la vignette
    fnx = marge + vignette_l / 2
    fny = situation_bas + bande_situation_h - 6.5 * mm
    c.setStrokeColor(HexColor("#000000"))
    c.setFillColor(HexColor("#000000"))
    c.setLineWidth(0.8)
    c.line(fnx, fny - 2 * mm, fnx, fny + 2.2 * mm)
    c.line(fnx, fny + 2.2 * mm, fnx - 1 * mm, fny + 0.6 * mm)
    c.line(fnx, fny + 2.2 * mm, fnx + 1 * mm, fny + 0.6 * mm)
    c.setFont("Helvetica-Bold", 5.5)
    c.drawCentredString(fnx, fny + 2.6 * mm, "N")

    # Grille de base : on regroupe des cellules voisines en îlots de taille
    # variable, puis on subdivise chaque îlot en 2-3 parcelles.
    marge_int_vignette = 2.2 * mm
    grille_x0 = marge + marge_int_vignette
    grille_y0 = situation_bas + 2 * mm
    grille_l = vignette_l - 2 * marge_int_vignette
    grille_h = bande_situation_h - 11 * mm
    cols_g, lignes_g = 5, 4
    cell_l = grille_l / cols_g
    cell_h = grille_h / lignes_g
    rue_marge = 0.9 * mm  # espace blanc entre îlots, figurant les rues

    occupe = [[False] * cols_g for _ in range(lignes_g)]
    ilots = []
    for j in range(lignes_g):
        for i in range(cols_g):
            if occupe[j][i]:
                continue
            formes_possibles = [(1, 1)]
            if i + 1 < cols_g and not occupe[j][i + 1]:
                formes_possibles.append((1, 2))
            if j + 1 < lignes_g and not occupe[j + 1][i]:
                formes_possibles.append((2, 1))
            if (i + 1 < cols_g and j + 1 < lignes_g
                    and not occupe[j][i + 1] and not occupe[j + 1][i] and not occupe[j + 1][i + 1]):
                formes_possibles.append((2, 2))
            span_l, span_c = alea_situation.choice(formes_possibles)
            for dj in range(span_l):
                for di in range(span_c):
                    occupe[j + dj][i + di] = True
            ilots.append((j, i, span_l, span_c))

    centre_grille = (lignes_g / 2, cols_g / 2)
    meilleur_ilot, meilleure_distance = None, None
    for (j, i, span_l, span_c) in ilots:
        cj, ci = j + span_l / 2, i + span_c / 2
        dist = (cj - centre_grille[0]) ** 2 + (ci - centre_grille[1]) ** 2
        if meilleure_distance is None or dist < meilleure_distance:
            meilleure_distance, meilleur_ilot = dist, (j, i, span_l, span_c)

    lettres_rues = ["RUE 12", "RUE 07", "VOIE A"]
    idx_rue = 0
    c.setFont("Helvetica", 3.6)

    for (j, i, span_l, span_c) in ilots:
        bx0 = grille_x0 + i * cell_l + rue_marge
        by0 = grille_y0 + j * cell_h + rue_marge
        bl = span_c * cell_l - 2 * rue_marge
        bh = span_l * cell_h - 2 * rue_marge

        # Découpage de l'îlot en 2 ou 3 parcelles, le long de son plus grand côté.
        n_parts = alea_situation.choice([2, 2, 3])
        horizontal = bl >= bh
        sous_parcelles = []
        if horizontal:
            largeur_part = bl / n_parts
            for k in range(n_parts):
                sous_parcelles.append((bx0 + k * largeur_part, by0, largeur_part, bh))
        else:
            hauteur_part = bh / n_parts
            for k in range(n_parts):
                sous_parcelles.append((bx0, by0 + k * hauteur_part, bl, hauteur_part))

        est_ilot_cible = (j, i, span_l, span_c) == meilleur_ilot
        index_cible = n_parts // 2

        for k, (px, py, pl, ph) in enumerate(sous_parcelles):
            est_cible = est_ilot_cible and k == index_cible
            c.setFillColor(HexColor("#FFFFFF"))
            c.setStrokeColor(HexColor("#000000"))
            c.setLineWidth(2.1 if est_cible else 0.3)
            c.rect(px, py, pl, ph, stroke=1, fill=0)

            if est_cible:
                ref_txt = parcelle.reference
                taille_police = 5.2
                c.setFont("Helvetica-Bold", taille_police)
                while c.stringWidth(ref_txt, "Helvetica-Bold", taille_police) > pl - 1 * mm and taille_police > 3.2:
                    taille_police -= 0.3
                if c.stringWidth(ref_txt, "Helvetica-Bold", taille_police) > pl - 1 * mm:
                    while len(ref_txt) > 4 and c.stringWidth(ref_txt + "…", "Helvetica-Bold", taille_police) > pl - 1 * mm:
                        ref_txt = ref_txt[:-1]
                    ref_txt += "…"
                c.setFont("Helvetica-Bold", taille_police)
                c.setFillColor(HexColor("#000000"))
                c.drawCentredString(px + pl / 2, py + ph / 2 - taille_police / 2.8, ref_txt)
            elif alea_situation.random() < 0.55:
                c.setFillColor(HexColor("#000000"))
                c.setFont("Helvetica", 3.6)
                numero = alea_situation.randint(4, 96)
                c.drawCentredString(px + pl / 2, py + ph / 2 - 1.2, str(numero))

        # Nom de rue, dans l'espace blanc sous certains îlots larges
        if span_c >= 2 and idx_rue < len(lettres_rues) and j + span_l < lignes_g:
            c.setFont("Helvetica-Oblique", 3.4)
            c.setFillColor(HexColor("#000000"))
            rue_y = grille_y0 + (j + span_l) * cell_h - rue_marge * 0.2
            c.drawCentredString(bx0 + bl / 2, rue_y, lettres_rues[idx_rue])
            idx_rue += 1

    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(HexColor("#000000"))
    c.drawCentredString(marge + vignette_l / 2, situation_bas - 4 * mm, "PLAN DE SITUATION")
    c.setFont("Helvetica", 6)
    c.drawCentredString(marge + vignette_l / 2, situation_bas - 7.6 * mm, "ÉCHELLE 1/4000e")

    # NORD + Superficie, à droite de la vignette
    fleche_x = marge + vignette_l + 14 * mm
    fleche_y = situation_bas + bande_situation_h - 9 * mm
    c.setStrokeColor(BLEU_NUIT)
    c.setFillColor(BLEU_NUIT)
    c.setLineWidth(1.3)
    c.line(fleche_x, fleche_y - 5 * mm, fleche_x, fleche_y + 5 * mm)
    c.line(fleche_x, fleche_y + 5 * mm, fleche_x - 1.8 * mm, fleche_y + 1.8 * mm)
    c.line(fleche_x, fleche_y + 5 * mm, fleche_x + 1.8 * mm, fleche_y + 1.8 * mm)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(fleche_x + 5 * mm, fleche_y - 3 * mm, "NORD")

    ares = int(float(parcelle.superficie_m2) // 100)
    centiares = float(parcelle.superficie_m2) - ares * 100
    superficie_trad = f"{ares}a {centiares:05.2f}ca".replace(".", ",")
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(BLEU_NUIT)
    c.drawRightString(largeur_page - marge, situation_bas + bande_situation_h - 10 * mm,
                       f"Superficie : {superficie_trad}")
    c.setFont("Helvetica", 8)
    c.setFillColor(GRIS)
    texte_m2 = f"({parcelle.superficie_m2:,.2f} m2)".replace(",", " ")
    base_m2, exposant_m2 = texte_m2[:-2], texte_m2[-2]  # sépare le "2" final du "2)"
    y_m2 = situation_bas + bande_situation_h - 16 * mm
    largeur_totale = c.stringWidth(base_m2, "Helvetica", 8) + c.stringWidth("2", "Helvetica", 6) + c.stringWidth(")", "Helvetica", 8)
    x_m2 = largeur_page - marge - largeur_totale
    c.drawString(x_m2, y_m2, base_m2)
    x_m2 += c.stringWidth(base_m2, "Helvetica", 8)
    c.setFont("Helvetica", 6)
    c.drawString(x_m2, y_m2 + 2.2, "2")
    x_m2 += c.stringWidth("2", "Helvetica", 6)
    c.setFont("Helvetica", 8)
    c.drawString(x_m2, y_m2, ")")

    y = situation_bas - 8 * mm

    # ---- Plan de bornage (aucun cadre : la parcelle est représentée directement) ----
    zone_hauteur = 78 * mm
    zone_bas = y - zone_hauteur

    marge_interne = 16 * mm
    zone_dispo_l = zone_largeur - 2 * marge_interne
    zone_dispo_h = zone_hauteur - 2 * marge_interne

    if mode_polygone:
        # ---- Tracé du vrai contour à partir des points de bornage saisis ----
        coords = [(float(p.x), float(p.y)) for p in points_bornage]
        xs = [cx for cx, _ in coords]
        ys = [cy for _, cy in coords]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        largeur_m = max(max_x - min_x, 0.01)
        hauteur_m = max(max_y - min_y, 0.01)

        echelle = min(zone_dispo_l / largeur_m, zone_dispo_h / hauteur_m)
        largeur_tracee = largeur_m * echelle
        hauteur_tracee = hauteur_m * echelle
        origine_x = marge + (zone_largeur - largeur_tracee) / 2
        origine_y = zone_bas + (zone_hauteur - hauteur_tracee) / 2

        def vers_page(px, py):
            return (
                origine_x + (px - min_x) * echelle,
                origine_y + (py - min_y) * echelle,
            )

        pts_page = [vers_page(cx, cy) for cx, cy in coords]
        centre_x = sum(p[0] for p in pts_page) / len(pts_page)
        centre_y = sum(p[1] for p in pts_page) / len(pts_page)

        def decaler_depuis_centre(px, py, distance):
            vx, vy = px - centre_x, py - centre_y
            norme = math.hypot(vx, vy) or 1
            return px + vx / norme * distance, py + vy / norme * distance

        # Contour rempli
        chemin = c.beginPath()
        chemin.moveTo(*pts_page[0])
        for px, py in pts_page[1:]:
            chemin.lineTo(px, py)
        chemin.close()
        c.setFillColor(HexColor("#FFFFFF"))
        c.setStrokeColor(BLEU_NUIT)
        c.setLineWidth(1.6)
        c.drawPath(chemin, stroke=1, fill=1)

        # Cotes réelles (distance entre bornes consécutives), au milieu de chaque côté
        nb = len(pts_page)
        c.setFont("Helvetica", 7.5)
        for i in range(nb):
            x1_m, y1_m = coords[i]
            x2_m, y2_m = coords[(i + 1) % nb]
            distance_reelle = math.hypot(x2_m - x1_m, y2_m - y1_m)
            mx = (pts_page[i][0] + pts_page[(i + 1) % nb][0]) / 2
            my = (pts_page[i][1] + pts_page[(i + 1) % nb][1]) / 2
            lx, ly = decaler_depuis_centre(mx, my, 6 * mm)
            c.setFillColor(GRIS)
            c.drawCentredString(lx, ly - 2, f"{distance_reelle:,.2f} m".replace(",", " "))

        # Bornes à chaque sommet, avec leur repère (B1, B2…)
        for i, (px, py) in enumerate(pts_page):
            c.setFillColor(OCRE)
            c.circle(px, py, 2 * mm, stroke=0, fill=1)
            label = points_bornage[i].label or f"B{i + 1}"
            lx, ly = decaler_depuis_centre(px, py, 8 * mm)
            c.setFillColor(BLEU_NUIT)
            c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString(lx, ly - 2, label)
    else:
        # ---- Repli : rectangle proportionné à la superficie enregistrée ----
        # (aucun point de bornage saisi pour cette parcelle)
        superficie = float(parcelle.superficie_m2)
        ratio = 4 / 3
        cote_a = math.sqrt(superficie * ratio)  # "largeur" en mètres
        cote_b = superficie / cote_a            # "hauteur" en mètres

        echelle = min(zone_dispo_l / cote_a, zone_dispo_h / cote_b)
        rect_l = cote_a * echelle
        rect_h = cote_b * echelle
        rect_x = marge + (zone_largeur - rect_l) / 2
        rect_y = zone_bas + (zone_hauteur - rect_h) / 2

        c.setFillColor(HexColor("#FFFFFF"))
        c.setStrokeColor(BLEU_NUIT)
        c.setLineWidth(1.6)
        c.rect(rect_x, rect_y, rect_l, rect_h, stroke=1, fill=1)

        # Bornes aux 4 coins
        c.setFillColor(OCRE)
        for cx, cy in [(rect_x, rect_y), (rect_x + rect_l, rect_y),
                       (rect_x, rect_y + rect_h), (rect_x + rect_l, rect_y + rect_h)]:
            c.circle(cx, cy, 2.2 * mm, stroke=0, fill=1)

        # Cotes (dimensions)
        c.setFillColor(GRIS)
        c.setFont("Helvetica", 8)
        c.drawCentredString(rect_x + rect_l / 2, rect_y - 6 * mm, f"≈ {cote_a:,.0f} m".replace(",", " "))
        c.saveState()
        c.translate(rect_x - 6 * mm, rect_y + rect_h / 2)
        c.rotate(90)
        c.drawCentredString(0, 0, f"≈ {cote_b:,.0f} m".replace(",", " "))
        c.restoreState()

    y = zone_bas - 8 * mm

    # ---- Certification (bas gauche) ----
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(BLEU_NUIT)
    c.drawString(marge, y, "Extrait certifié conforme")
    y -= 5 * mm
    c.setFont("Helvetica", 8.5)
    c.setFillColor(GRIS)
    c.drawString(marge, y, f"Thiès, le {date.today().strftime('%d/%m/%Y')}")
    y -= 5 * mm
    c.drawString(marge, y, "Le Chef du Bureau du Cadastre")

    if mode_polygone:
        echelle_brute = 2834.64 / echelle  # dénominateur d'échelle approximatif
        paliers = [100, 200, 250, 500, 1000, 2000, 2500, 5000]
        denom = min(paliers, key=lambda p: abs(p - echelle_brute))
        echelle_txt = f"1 / {denom}"
    else:
        echelle_txt = "indicative"

    # ---- Échelle, tout au fond de la page, centrée ----
    echelle_y = cadre_bas + 6 * mm
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(BLEU_NUIT)
    c.drawCentredString(largeur_page / 2, echelle_y, f"ÉCHELLE = {echelle_txt}")

    c.showPage()
    c.save()
    buffer.seek(0)

    filename = f"extrait-plan-{parcelle.reference}.pdf"
    telecharger = request.GET.get("telecharger") == "1"
    return FileResponse(buffer, as_attachment=telecharger, filename=filename)


# ==========================================================================
# Gestion des actualités (réservée aux agents/administrateurs)
# ==========================================================================

@agent_requis
def gestion_actualites(request):
    actualites = Actualite.objects.all()
    return render(request, "core/gestion_actualites.html", {"actualites": actualites})


@agent_requis
def creer_actualite(request):
    if request.method == "POST":
        form = ActualiteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Actualité créée avec succès.")
            return redirect("core:gestion_actualites")
    else:
        form = ActualiteForm()
    return render(request, "core/form_actualite.html", {"form": form, "creation": True})


@agent_requis
def modifier_actualite(request, pk):
    actualite = get_object_or_404(Actualite, pk=pk)
    if request.method == "POST":
        form = ActualiteForm(request.POST, instance=actualite)
        if form.is_valid():
            form.save()
            messages.success(request, "Actualité mise à jour.")
            return redirect("core:gestion_actualites")
    else:
        form = ActualiteForm(instance=actualite)
    return render(request, "core/form_actualite.html", {
        "form": form, "creation": False, "actualite": actualite,
    })


@agent_requis
def supprimer_actualite(request, pk):
    actualite = get_object_or_404(Actualite, pk=pk)
    if request.method == "POST":
        actualite.delete()
        messages.success(request, "Actualité supprimée.")
        return redirect("core:gestion_actualites")
    return render(request, "core/confirmer_suppression.html", {
        "objet": actualite, "titre_page": "Supprimer cette actualité ?",
        "url_annuler": "core:gestion_actualites",
    })


# ==========================================================================
# Gestion des sections du guide du visiteur (réservée aux agents/administrateurs)
# ==========================================================================

@agent_requis
def gestion_guide(request):
    sections = SectionGuide.objects.all()
    return render(request, "core/gestion_guide.html", {"sections": sections})


@agent_requis
def deplacer_section_guide(request, pk, direction):
    section = get_object_or_404(SectionGuide, pk=pk)
    if request.method == "POST":
        if direction == "haut":
            voisine = (
                SectionGuide.objects.filter(ordre__lt=section.ordre)
                .order_by("-ordre", "-id").first()
            )
        else:
            voisine = (
                SectionGuide.objects.filter(ordre__gt=section.ordre)
                .order_by("ordre", "id").first()
            )
        if voisine:
            section.ordre, voisine.ordre = voisine.ordre, section.ordre
            section.save(update_fields=["ordre"])
            voisine.save(update_fields=["ordre"])
    return redirect("core:gestion_guide")


@agent_requis
def basculer_publication_section_guide(request, pk):
    section = get_object_or_404(SectionGuide, pk=pk)
    if request.method == "POST":
        section.publie = not section.publie
        section.save(update_fields=["publie"])
    return redirect("core:gestion_guide")


@agent_requis
def creer_section_guide(request):
    if request.method == "POST":
        form = SectionGuideForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Section créée avec succès.")
            return redirect("core:gestion_guide")
    else:
        nombre_sections = SectionGuide.objects.count()
        form = SectionGuideForm(initial={"ordre": (nombre_sections + 1) * 10})
    return render(request, "core/form_section_guide.html", {"form": form, "creation": True})


@agent_requis
def modifier_section_guide(request, pk):
    section = get_object_or_404(SectionGuide, pk=pk)
    if request.method == "POST":
        form = SectionGuideForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, "Section mise à jour.")
            return redirect("core:gestion_guide")
    else:
        form = SectionGuideForm(instance=section)
    return render(request, "core/form_section_guide.html", {
        "form": form, "creation": False, "section": section,
    })


@agent_requis
def supprimer_section_guide(request, pk):
    section = get_object_or_404(SectionGuide, pk=pk)
    if request.method == "POST":
        section.delete()
        messages.success(request, "Section supprimée.")
        return redirect("core:gestion_guide")
    return render(request, "core/confirmer_suppression.html", {
        "objet": section, "titre_page": "Supprimer cette section ?",
        "url_annuler": "core:gestion_guide",
    })


def simulateur_taxe(request):
    """Simulateur public : estime la valeur vénale et la taxe foncière d'une
    parcelle à partir de sa superficie et de son usage, avec les mêmes prix
    au m² et taux que ceux utilisés par la plateforme (voir PRIX_M2_PAR_USAGE
    et TAUX_PAR_USAGE) — sur les données fictives de démonstration.

    Une fourchette (±15 %) est affichée plutôt qu'un chiffre unique : la
    valeur vénale réelle d'un terrain varie toujours selon son emplacement
    précis, sa forme, son état de viabilisation, etc., qu'un simulateur ne
    peut pas connaître.
    """
    resultat = None
    superficie = request.GET.get("superficie", "")
    usage = request.GET.get("usage", "")

    if superficie and usage in PRIX_M2_PAR_USAGE:
        try:
            superficie_decimale = Decimal(superficie)
            if superficie_decimale <= 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            messages.error(request, "Indiquez une superficie valide, supérieure à 0 m².")
        else:
            prix_m2 = PRIX_M2_PAR_USAGE[usage]
            taux = TAUX_PAR_USAGE[usage]
            valeur_centrale = superficie_decimale * prix_m2
            valeur_min = (valeur_centrale * Decimal("0.85")).quantize(Decimal("1"))
            valeur_max = (valeur_centrale * Decimal("1.25")).quantize(Decimal("1"))
            resultat = {
                "superficie": superficie_decimale,
                "usage_libelle": dict(Parcelle.USAGE_CHOICES).get(usage, usage),
                "prix_m2": prix_m2,
                "taux": taux,
                "taux_pourcentage": (taux * 100).normalize(),
                "valeur_min": valeur_min,
                "valeur_max": valeur_max,
                "taxe_min": (valeur_min * taux).quantize(Decimal("1")),
                "taxe_max": (valeur_max * taux).quantize(Decimal("1")),
            }

    return render(request, "core/simulateur_taxe.html", {
        "resultat": resultat,
        "usage_choices": Parcelle.USAGE_CHOICES,
        "superficie_saisie": superficie,
        "usage_saisi": usage,
    })


def modeles_documents(request):
    """Page publique listant les modèles de documents (Word) téléchargeables
    pour préparer une démarche avant de déposer un dossier en ligne."""
    return render(request, "core/modeles_documents.html")


def annuaire_services(request):
    """Page publique listant les services utiles pour les démarches
    cadastrales et fiscales dans la région de Thiès. Coordonnées vérifiées
    auprès de sources officielles (dgid.sn, senegalservices.sn) — voir la
    note de source en bas de page."""
    return render(request, "core/annuaire_services.html")


@administrateur_requis
def journal_activite(request):
    """Historique des actions importantes effectuées par les agents (émission
    de taxe, paiement, dossier traité, rendez-vous confirmé…) — réservé aux
    administrateurs, pour la traçabilité et la responsabilisation."""
    entrees = JournalActivite.objects.select_related("agent").all()

    agent_id = request.GET.get("agent", "").strip()
    if agent_id:
        entrees = entrees.filter(agent_id=agent_id)

    from django.contrib.auth.models import User
    agents = User.objects.filter(actions_journal__isnull=False).distinct().order_by("username")

    paginator = Paginator(entrees, 30)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "core/journal_activite.html", {
        "page_obj": page_obj, "agents": agents, "agent_selectionne": agent_id,
    })

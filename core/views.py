from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Count
from django.http import FileResponse, JsonResponse
from django.urls import reverse
import io
import math
from datetime import date

from cadastre.models import Parcelle, Commune
from fiscalite.models import TaxeFonciere
from .models import Actualite


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


def a_propos(request):
    return render(request, "core/a_propos.html")


def guide_cadastre(request):
    """Page pédagogique publique : cadastre, immatriculation, valeur vénale et taxe foncière."""
    return render(request, "core/guide_cadastre.html")


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


def carte_parcelles(request):
    """Carte interactive publique des parcelles géolocalisées (Leaflet)."""
    return render(request, "core/carte_parcelles.html", {
        "communes": Commune.objects.all(),
        "statut_choices": Parcelle.STATUT_CHOICES,
        "usage_choices": Parcelle.USAGE_CHOICES,
    })


def carte_parcelles_donnees(request):
    """Renvoie en JSON les parcelles géolocalisées, pour affichage sur la carte.

    Vue publique : par souci de confidentialité, aucune information sur le
    propriétaire n'est transmise ici (uniquement des données déjà visibles
    via la consultation publique par référence).
    """
    parcelles = Parcelle.objects.select_related("commune").filter(
        latitude__isnull=False, longitude__isnull=False
    )

    commune_id = request.GET.get("commune", "").strip()
    statut = request.GET.get("statut", "").strip()
    usage = request.GET.get("usage", "").strip()
    if commune_id:
        parcelles = parcelles.filter(commune_id=commune_id)
    if statut:
        parcelles = parcelles.filter(statut=statut)
    if usage:
        parcelles = parcelles.filter(usage=usage)

    donnees = [
        {
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
            "url_consultation": f"{reverse('core:consultation_publique')}?reference={p.reference}",
            "url_plan": reverse("core:extrait_plan", args=[p.reference]),
        }
        for p in parcelles
    ]
    return JsonResponse({"parcelles": donnees, "total": len(donnees)})


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

    parcelle = get_object_or_404(Parcelle, reference__iexact=reference)

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

    # ---- Bandeau tricolore (fine bande décorative en haut du cadre) ----
    bande_h = 5 * mm
    tiers = bande_h / 3
    haut_bande = hauteur_page - cadre_marge - 2 * mm
    largeur_bande = largeur_page - 2 * cadre_marge - 4 * mm
    c.setFillColor(VERT)
    c.rect(cadre_marge + 2 * mm, haut_bande - tiers, largeur_bande, tiers, stroke=0, fill=1)
    c.setFillColor(OR)
    c.rect(cadre_marge + 2 * mm, haut_bande - 2 * tiers, largeur_bande, tiers, stroke=0, fill=1)
    c.setFillColor(ROUGE)
    c.rect(cadre_marge + 2 * mm, haut_bande - 3 * tiers, largeur_bande, tiers, stroke=0, fill=1)

    y = haut_bande - bande_h - 6 * mm

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

    bande_situation_h = 32 * mm
    situation_bas = y - bande_situation_h

    # Vignette "Plan de situation" (schématique, non géoréférencée)
    vignette_l = 36 * mm
    c.setFillColor(SABLE)
    c.rect(marge, situation_bas, vignette_l, bande_situation_h, stroke=0, fill=1)
    c.setStrokeColor(BLEU_NUIT)
    c.setLineWidth(0.8)
    c.rect(marge, situation_bas, vignette_l, bande_situation_h, stroke=1, fill=0)
    c.setStrokeColor(HexColor("#B9AF98"))
    c.setLineWidth(0.5)
    cols_v, lignes_v = 4, 3
    case_l = vignette_l / cols_v
    case_h = (bande_situation_h - 6 * mm) / lignes_v
    for i in range(cols_v):
        for j in range(lignes_v):
            cx0 = marge + i * case_l + 1 * mm
            cy0 = situation_bas + 5 * mm + j * case_h + 1 * mm
            c.rect(cx0, cy0, case_l - 2 * mm, case_h - 2 * mm, stroke=1, fill=0)
    c.setFillColor(OCRE)
    hx = marge + 1 * case_l + 1 * mm
    hy = situation_bas + 5 * mm + 1 * case_h + 1 * mm
    c.rect(hx, hy, case_l - 2 * mm, case_h - 2 * mm, stroke=0, fill=1)
    c.setFont("Helvetica-Oblique", 6)
    c.setFillColor(GRIS)
    c.drawCentredString(marge + vignette_l / 2, situation_bas - 3.2 * mm, "Plan de situation (schématique)")

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

    # ---- Plan de bornage ----
    zone_hauteur = 78 * mm
    zone_bas = y - zone_hauteur
    c.setFillColor(SABLE)
    c.rect(marge, zone_bas, zone_largeur, zone_hauteur, stroke=0, fill=1)
    c.setStrokeColor(BLEU_NUIT)
    c.setLineWidth(0.8)
    c.rect(marge, zone_bas, zone_largeur, zone_hauteur, stroke=1, fill=0)

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

    c.setFont("Helvetica-Oblique", 7.5)
    c.setFillColor(GRIS)
    if mode_polygone:
        c.drawString(marge, y, "Plan tracé à partir des coordonnées de bornage saisies dans la plateforme —")
        y -= 4 * mm
        c.drawString(marge, y, "à visée pédagogique, ne remplace pas un plan de bornage officiel établi par un géomètre agréé.")
    else:
        c.drawString(marge, y, "Schéma généré automatiquement à partir de la superficie enregistrée — non géoréférencé,")
        y -= 4 * mm
        c.drawString(marge, y, "ne remplace pas un plan de bornage officiel établi par un géomètre agréé.")

    # ---- Certification (bas gauche) ----
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(BLEU_NUIT)
    c.drawString(marge, y, "Extrait certifié conforme")
    y -= 5 * mm
    c.setFont("Helvetica", 8.5)
    c.setFillColor(GRIS)
    c.drawString(marge, y, f"Thiès, le {date.today().strftime('%d/%m/%Y')}")
    y -= 5 * mm
    c.drawString(marge, y, "Le Chef du Bureau du Cadastre")

    # ---- Tampon officiel ----
    sx, sy = marge + 22 * mm, y - 18 * mm
    c.setStrokeColor(ROUGE)
    c.setLineWidth(1.2)
    c.circle(sx, sy, 15 * mm, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(ROUGE)
    c.drawCentredString(sx, sy + 2 * mm, "CADASTRE")
    c.drawCentredString(sx, sy - 4 * mm, "THIÈS")

    # ---- Encadré "plan" (bas droite), à la façon d'un cartouche de titre foncier ----
    encadre_l = 62 * mm
    encadre_h = 28 * mm
    encadre_x = largeur_page - marge - encadre_l
    encadre_y = sy - 15 * mm
    c.setStrokeColor(BLEU_NUIT)
    c.setLineWidth(0.8)
    c.rect(encadre_x, encadre_y, encadre_l, encadre_h, stroke=1, fill=0)

    if mode_polygone:
        echelle_brute = 2834.64 / echelle  # dénominateur d'échelle approximatif
        paliers = [100, 200, 250, 500, 1000, 2000, 2500, 5000]
        denom = min(paliers, key=lambda p: abs(p - echelle_brute))
        echelle_txt = f"1 / {denom}"
    else:
        echelle_txt = "indicative"

    lignes_encadre = [
        f"Plan de la parcelle {parcelle.reference}",
        f"Échelle : {echelle_txt}",
        f"Dossier n° {parcelle.pk:06d}",
    ]
    ey = encadre_y + encadre_h - 7 * mm
    c.setFont("Helvetica", 8)
    c.setFillColor(BLEU_NUIT)
    for ligne in lignes_encadre:
        c.drawCentredString(encadre_x + encadre_l / 2, ey, ligne)
        ey -= 6 * mm

    # ---- Pied de page ----
    footer_y = encadre_y - 8 * mm
    c.setFont("Helvetica", 7.5)
    c.setFillColor(GRIS)
    c.drawCentredString(
        largeur_page / 2, footer_y,
        "Document généré depuis la plateforme Cadastre & Fiscalité foncière — Thiès — "
        "données à caractère fictif (plateforme de démonstration)."
    )

    c.showPage()
    c.save()
    buffer.seek(0)

    filename = f"extrait-plan-{parcelle.reference}.pdf"
    telecharger = request.GET.get("telecharger") == "1"
    return FileResponse(buffer, as_attachment=telecharger, filename=filename)

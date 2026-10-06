import csv

from django.http import HttpResponse


def generer_recu_pdf(titre, sous_titre, reference, lignes, filename):
    """Génère un reçu PDF simple (référence + quelques lignes d'information)
    — utilisé pour confirmer le dépôt d'un dossier ou d'une demande de
    rendez-vous. lignes : liste de tuples (libellé, valeur)."""
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    from django.http import FileResponse

    BLEU_NUIT = HexColor("#1B2A4A")
    GRIS = HexColor("#4B5262")
    SABLE = HexColor("#F7F4EE")
    BLANC = HexColor("#FFFFFF")
    BORDURE = HexColor("#E2D9C8")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largeur, hauteur = A4
    marge = 22 * mm

    c.setFillColor(BLEU_NUIT)
    c.rect(0, hauteur - 30 * mm, largeur, 30 * mm, fill=1, stroke=0)
    c.setFillColor(BLANC)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(marge, hauteur - 14 * mm, "CADASTRE & FISCALITÉ FONCIÈRE")
    c.setFont("Helvetica", 9)
    c.drawString(marge, hauteur - 20 * mm, "Région de Thiès")

    y = hauteur - 42 * mm
    c.setFillColor(BLEU_NUIT)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(marge, y, titre)
    y -= 7 * mm
    c.setFillColor(GRIS)
    c.setFont("Helvetica", 10)
    c.drawString(marge, y, sous_titre)

    y -= 12 * mm
    c.setFillColor(SABLE)
    c.rect(marge, y - 14 * mm, largeur - 2 * marge, 14 * mm, fill=1, stroke=0)
    c.setFillColor(BLEU_NUIT)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(largeur / 2, y - 9 * mm, reference)

    y -= 26 * mm
    for libelle, valeur in lignes:
        c.setFont("Helvetica", 10)
        c.setFillColor(GRIS)
        c.drawString(marge, y, f"{libelle} :")
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(BLEU_NUIT)
        c.drawString(marge + 55 * mm, y, str(valeur))
        y -= 8 * mm

    y -= 6 * mm
    c.setStrokeColor(BORDURE)
    c.line(marge, y, largeur - marge, y)
    y -= 8 * mm
    c.setFillColor(GRIS)
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(
        marge, y,
        "Ce reçu confirme l'enregistrement de votre demande. Conservez la référence ci-dessus pour suivre son statut.",
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=filename)


def reponse_csv(nom_fichier, entetes, lignes):
    """Construit une réponse HTTP de type fichier CSV téléchargeable.

    entetes : liste des noms de colonnes.
    lignes : liste de lignes, chaque ligne étant une liste de valeurs dans
    le même ordre que les en-têtes.

    Utilisé pour les boutons "Exporter" des listes de parcelles, taxes et
    dossiers, afin de ne pas dupliquer cette logique dans chaque app.
    """
    reponse = HttpResponse(content_type="text/csv; charset=utf-8")
    reponse["Content-Disposition"] = f'attachment; filename="{nom_fichier}"'
    # BOM pour un affichage correct des accents dans Excel.
    reponse.write("\ufeff")
    # Point-virgule plutôt que virgule : c'est le séparateur attendu par la
    # version française d'Excel (la virgule y est le séparateur décimal).
    ecrivain = csv.writer(reponse, delimiter=";")
    ecrivain.writerow(entetes)
    ecrivain.writerows(lignes)
    return reponse

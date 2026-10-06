import json
import random
import unicodedata
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from cadastre.models import Commune, Proprietaire, Parcelle, PointBornage
from fiscalite.models import TaxeFonciere, TAUX_PAR_USAGE

NOM_TABLE_SOURCE = "BD_zone_nguinth"
SRID_SOURCE = 32628  # UTM zone 28N (Sénégal) — unités en mètres

# --- Valeurs FICTIVES, faute de données réelles disponibles pour ces champs ---
# (mêmes ordres de grandeur que la commande peupler_donnees, pour rester cohérent)
VALEUR_M2_PAR_USAGE = {
    "RESIDENTIEL": 25000, "COMMERCIAL": 55000, "AGRICOLE": 4000,
    "INDUSTRIEL": 35000, "MIXTE": 30000,
}
# Zone à dominante résidentielle : on pondère fortement dans ce sens.
USAGES_PONDERES = (
    ["RESIDENTIEL"] * 70 + ["COMMERCIAL"] * 15 + ["MIXTE"] * 10
    + ["AGRICOLE"] * 3 + ["INDUSTRIEL"] * 2
)


def simplifier(texte):
    """Retire accents/casse pour permettre une recherche de colonne tolérante."""
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("ascii")
    return texte.lower()


def extraire_contour_carte(geojson_texte):
    """Convertit le GeoJSON (WGS84) d'une géométrie en une liste de points
    [latitude, longitude] représentant son anneau extérieur, prête à être
    dessinée telle quelle sur la carte interactive (Leaflet).

    Ne garde que le premier polygone et son anneau extérieur (pas les trous
    ni les éventuels polygones supplémentaires d'un MultiPolygon) : une
    simplification suffisante pour l'affichage sur la carte, dans le même
    esprit que l'extraction du contour métrique utilisée plus haut pour le
    plan de bornage.
    """
    if not geojson_texte:
        return None
    try:
        geometrie = json.loads(geojson_texte)
    except (TypeError, ValueError):
        return None

    type_geometrie = geometrie.get("type")
    coordonnees = geometrie.get("coordinates")
    if type_geometrie == "Polygon" and coordonnees:
        anneau_exterieur = coordonnees[0]
    elif type_geometrie == "MultiPolygon" and coordonnees:
        anneau_exterieur = coordonnees[0][0]
    else:
        return None

    # GeoJSON donne les points en [longitude, latitude] ; Leaflet attend
    # [latitude, longitude]. Le dernier point d'un anneau fermé répète le
    # premier : on l'enlève (Leaflet referme le polygone tout seul).
    points = [[lat, lon] for lon, lat in anneau_exterieur]
    if len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]
    return points or None


def trouver_colonne(colonnes, *mots_cles):
    """Trouve, parmi les colonnes réelles de la table source, celle qui contient
    tous les mots-clés donnés (peu importe accents/casse/troncature d'affichage)."""
    mots_cles_simples = [simplifier(m) for m in mots_cles]
    for col in colonnes:
        col_simple = simplifier(col)
        if all(mot in col_simple for mot in mots_cles_simples):
            return col
    raise CommandError(
        f"Impossible de trouver une colonne contenant {mots_cles!r}.\n"
        f"Colonnes disponibles dans \"{NOM_TABLE_SOURCE}\" : {colonnes}"
    )


class Command(BaseCommand):
    help = (
        "Importe les vraies parcelles de la table externe BD_zone_nguinth "
        "(PostGIS) vers les modèles Commune/Proprietaire/Parcelle/PointBornage. "
        "Les champs absents de la source (valeur vénale, usage) sont générés "
        "fictivement ; le statut d'immatriculation est déduit de la présence "
        "d'un numéro de titre foncier."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limite", type=int, default=None,
            help="N'importer que les N premières lignes (pour tester avant l'import complet).",
        )
        parser.add_argument(
            "--sans-taxes", action="store_true",
            help="Ne pas générer d'avis de taxe foncière fictifs pour les parcelles importées.",
        )
        parser.add_argument(
            "--remplacer", action="store_true",
            help=(
                "Supprimer d'abord les parcelles déjà importées pour la commune "
                "\"Nguinth\" avant de réimporter (évite les doublons si la "
                "commande a déjà été exécutée, par exemple après une mise à jour "
                "de cette commande)."
            ),
        )

    def handle(self, *args, **options):
        limite = options["limite"]
        avec_taxes = not options["sans_taxes"]

        if options["remplacer"]:
            nb_supprimees, _ = Parcelle.objects.filter(commune__nom="Nguinth").delete()
            if nb_supprimees:
                self.stdout.write(f"{nb_supprimees} enregistrement(s) lié(s) à d'anciennes parcelles \"Nguinth\" supprimé(s).")

        with connection.cursor() as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = %s ORDER BY ordinal_position",
                [NOM_TABLE_SOURCE],
            )
            colonnes = [row[0] for row in cur.fetchall()]

        if not colonnes:
            raise CommandError(
                f'Table "{NOM_TABLE_SOURCE}" introuvable (ou vide de colonnes). '
                "Vérifie le nom exact de la table dans ta base."
            )

        col_nicad = trouver_colonne(colonnes, "nicad")
        col_nom = trouver_colonne(colonnes, "nom", "pr")
        col_superficie = trouver_colonne(colonnes, "superficie")
        col_nin = trouver_colonne(colonnes, "nin")
        col_titre = trouver_colonne(colonnes, "titre")
        col_designation = trouver_colonne(colonnes, "designation")
        col_lot = trouver_colonne(colonnes, "lot")

        self.stdout.write("Colonnes détectées :")
        for label, col in [
            ("N° Nicad", col_nicad), ("Nom et Prénom", col_nom),
            ("Superficie m²", col_superficie), ("NIN", col_nin),
            ("N° Titre Foncier", col_titre), ("Désignation des lieux", col_designation),
            ("N° Lot", col_lot),
        ]:
            self.stdout.write(f"  - {label} -> \"{col}\"")

        sql = f"""
            SELECT
                id,
                "{col_nicad}"        AS nicad,
                "{col_nom}"          AS nom,
                "{col_superficie}"   AS superficie,
                "{col_nin}"          AS nin,
                "{col_titre}"        AS titre_foncier,
                "{col_designation}"  AS designation,
                "{col_lot}"          AS lot,
                ST_Y(ST_Centroid(ST_Transform(geom, 4326))) AS latitude,
                ST_X(ST_Centroid(ST_Transform(geom, 4326))) AS longitude,
                ST_Area(geom) AS superficie_geom,
                ST_AsText(ST_ExteriorRing(ST_GeometryN(geom, 1))) AS contour_wkt,
                ST_AsGeoJSON(ST_Transform(geom, 4326)) AS contour_wgs84_geojson
            FROM "{NOM_TABLE_SOURCE}"
            ORDER BY id
        """
        if limite:
            sql += f" LIMIT {int(limite)}"

        with connection.cursor() as cur:
            cur.execute(sql)
            lignes = cur.fetchall()

        self.stdout.write(f"{len(lignes)} lignes lues depuis \"{NOM_TABLE_SOURCE}\".")

        with transaction.atomic():
            commune, cree = Commune.objects.get_or_create(
                nom="Nguinth", defaults={"population_estimee": None}
            )
            if cree:
                self.stdout.write("Commune \"Nguinth\" créée.")

            references_utilisees = set(
                Parcelle.objects.values_list("reference", flat=True)
            )
            proprietaires_cache = {}
            nb_creees, nb_ignorees, nb_superficie_calculee, nb_sans_contour = 0, 0, 0, 0

            for (
                id_source, nicad, nom, superficie, nin, titre_foncier,
                designation, lot, latitude, longitude, superficie_geom, contour_wkt,
                contour_wgs84_geojson,
            ) in lignes:

                # --- Référence cadastrale : Nicad en priorité, sinon repli ---
                reference = (nicad or "").strip()
                if not reference:
                    reference = (lot or "").strip()
                if not reference:
                    reference = f"NGUINTH-{id_source}"
                # Le "/" casse le routage Django (URLs des plans/de la carte) : on le
                # remplace, certaines références réelles (Nicad, titres fonciers) en
                # contenant parfois (ex. "1234/DGID").
                reference = reference.replace("/", "-")
                reference = reference[:30]
                if reference in references_utilisees:
                    reference = f"{reference[:24]}-{id_source}"[:30]
                references_utilisees.add(reference)

                # --- Superficie : valeur officielle si renseignée, sinon calculée
                #     directement à partir du vrai polygone (ST_Area) ---
                superficie_attribut = None
                if superficie is not None:
                    try:
                        if float(superficie) > 0:
                            superficie_attribut = float(superficie)
                    except (TypeError, ValueError):
                        pass

                if superficie_attribut is not None:
                    superficie_finale = superficie_attribut
                elif superficie_geom is not None and superficie_geom > 0:
                    superficie_finale = superficie_geom
                    nb_superficie_calculee += 1
                else:
                    superficie_finale = None

                if superficie_finale is None:
                    nb_ignorees += 1
                    continue

                # --- Propriétaire : regroupé par NIN si connu, sinon par nom ---
                nin_propre = (nin or "").strip()
                nom_propre = (nom or "Propriétaire non renseigné").strip()
                cle_proprio = nin_propre or f"nom:{nom_propre.lower()}"
                proprietaire = proprietaires_cache.get(cle_proprio)
                if proprietaire is None:
                    proprietaire, _ = Proprietaire.objects.get_or_create(
                        nin_ou_rccm=nin_propre,
                        nom_complet=nom_propre,
                        defaults={"type_proprietaire": "PHYSIQUE"},
                    )
                    proprietaires_cache[cle_proprio] = proprietaire

                # --- Champs déduits ou fictifs (voir help de la commande) ---
                statut = "IMMATRICULEE" if (titre_foncier or "").strip() else "NON_IMMATRICULEE"
                usage = random.choice(USAGES_PONDERES)
                superficie_dec = Decimal(str(round(superficie_finale, 2)))
                valeur_m2 = VALEUR_M2_PAR_USAGE[usage]
                valeur_venale = (
                    superficie_dec * valeur_m2 * Decimal(str(round(random.uniform(0.85, 1.25), 3)))
                ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

                parcelle = Parcelle.objects.create(
                    reference=reference,
                    commune=commune,
                    proprietaire=proprietaire,
                    quartier=(designation or "Nguinth").strip()[:120] or "Nguinth",
                    superficie_m2=superficie_dec,
                    valeur_venale_fcfa=valeur_venale,
                    usage=usage,
                    statut=statut,
                    latitude=Decimal(str(round(latitude, 6))) if latitude is not None else None,
                    longitude=Decimal(str(round(longitude, 6))) if longitude is not None else None,
                    contour_carte=extraire_contour_carte(contour_wgs84_geojson),
                )
                nb_creees += 1
                if parcelle.contour_carte is None:
                    nb_sans_contour += 1

                # --- Points de bornage : vrai contour issu de la géométrie PostGIS ---
                if contour_wkt:
                    points_texte = contour_wkt.replace("LINESTRING(", "").replace(")", "")
                    sommets = [p.strip().split(" ") for p in points_texte.split(",") if p.strip()]
                    # Le dernier point d'un contour fermé répète le premier : on l'enlève.
                    if len(sommets) > 1 and sommets[0] == sommets[-1]:
                        sommets = sommets[:-1]
                    for ordre, (x, y) in enumerate(sommets, start=1):
                        PointBornage.objects.create(
                            parcelle=parcelle, ordre=ordre,
                            x=Decimal(str(round(float(x), 2))),
                            y=Decimal(str(round(float(y), 2))),
                        )

                # --- Taxe foncière fictive (facultatif) ---
                if avec_taxes:
                    annee = 2026
                    taux = TAUX_PAR_USAGE[usage]
                    montant_du = (valeur_venale * taux).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                    TaxeFonciere.objects.create(
                        parcelle=parcelle, annee=annee, taux_applique=taux,
                        montant_du=montant_du, date_limite=date(annee, 12, 31),
                        statut="EMISE",
                    )

        self.stdout.write(self.style.SUCCESS(
            f"Import terminé : {nb_creees} parcelles créées, {nb_ignorees} lignes ignorées "
            f"(ni superficie renseignée, ni géométrie exploitable)."
        ))
        self.stdout.write(
            f"Superficie calculée depuis la géométrie (colonne absente) pour "
            f"{nb_superficie_calculee} parcelle(s) sur {nb_creees}."
        )
        self.stdout.write(
            f"Contour réel exploitable pour la carte interactive : "
            f"{nb_creees - nb_sans_contour} parcelle(s) sur {nb_creees} "
            f"({nb_sans_contour} sans géométrie de polygone exploitable, affichées "
            f"par un point sur la carte)."
        )
        self.stdout.write(
            "Rappel : valeur vénale et usage sont FICTIFS (non présents dans la source). "
            "Le statut d'immatriculation est déduit de la présence d'un n° de titre foncier."
        )

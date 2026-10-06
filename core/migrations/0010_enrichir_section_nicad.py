from django.db import migrations

TITRE = "Qu'est-ce que le NICAD ?"

CONTENU = (
    "Le NICAD (Numéro d'Identification Cadastrale) est un identifiant unique et "
    "obligatoire attribué à chaque parcelle de terrain au Sénégal, quel que soit "
    "son statut juridique. Institué par le décret n° 2012-396 du 27 mars 2012, il "
    "met fin à la juxtaposition d'anciens systèmes de repérage (numéro de titre "
    "foncier, numéro de lot, référence de bail) qui entretenait confusion et "
    "litiges.\n\n"
    "Le NICAD est délivré gratuitement par le bureau du cadastre territorialement "
    "compétent, sous la forme d'un Certificat d'Identification Cadastrale (CIC), "
    "généralement dans un délai de 5 jours ouvrés. Ce certificat reste valable 6 "
    "mois.\n\n"
    "Un point important à retenir : le NICAD n'est pas la même chose que le titre "
    "foncier. Une parcelle peut très bien avoir un NICAD sans être encore "
    "immatriculée (par exemple un terrain du domaine national ou une parcelle "
    "dont la procédure d'immatriculation est en cours). En revanche, tout titre "
    "foncier délivré aujourd'hui doit obligatoirement être associé à un "
    "NICAD.\n\n"
    "Comment un NICAD est-il construit ? L'article 3 du décret précise qu'il "
    "comporte 16 chiffres, répartis en deux parties :\n"
    "- RR DD AA CC (8 chiffres) : la localisation administrative de la parcelle "
    "— Région, Département, Arrondissement, Commune (ou commune "
    "d'arrondissement, ou communauté rurale) — selon le système de "
    "codification des localités (SYSCOL) en vigueur au Sénégal.\n"
    "- SSS PPPPP (8 chiffres) : la situation de la parcelle au sein de cette "
    "commune — sa section cadastrale (3 chiffres), puis son numéro propre au "
    "sein de cette section (5 chiffres).\n\n"
    "Prenons un exemple réel, tiré d'une parcelle de la zone de Nguinth (commune "
    "de Thiès Nord) : 0723011103100543. Décomposé selon cette structure, cela "
    "donne 07 · 23 · 01 · 11 · 031 · 00543 — les quatre premiers segments "
    "situent administrativement le terrain (jusqu'à la commune), les deux "
    "derniers désignent la section cadastrale puis la parcelle elle-même au "
    "sein de cette section. Cette décomposition est d'ailleurs affichée "
    "automatiquement sur cette plateforme pour toute parcelle dont la "
    "référence suit ce format à 16 chiffres (voir la consultation publique ou "
    "la fiche d'une parcelle)."
)


def enrichir_section(apps, schema_editor):
    SectionGuide = apps.get_model("core", "SectionGuide")
    SectionGuide.objects.filter(titre=TITRE).update(contenu=CONTENU)


def revenir_en_arriere(apps, schema_editor):
    # Pas de retour automatique à l'ancien texte : la version précédente
    # (moins détaillée) n'est pas reconstituée en cas de "migrate" arrière.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_seed_sections_fiscalite_reelle"),
    ]

    operations = [
        migrations.RunPython(enrichir_section, revenir_en_arriere),
    ]

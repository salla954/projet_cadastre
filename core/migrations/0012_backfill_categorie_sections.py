from django.db import migrations

# Classement des sections déjà en base au moment de l'introduction du champ
# "categorie". Une nouvelle section créée par un agent après cette migration
# devra choisir sa rubrique elle-même (ou restera dans la rubrique par défaut
# "Comprendre le cadastre").
CATEGORIES_PAR_TITRE = {
    "Qu'est-ce que le cadastre ?": "COMPRENDRE",
    "Qu'est-ce que le NICAD ?": "COMPRENDRE",
    "Qu'est-ce que l'immatriculation ?": "COMPRENDRE",
    "Domaine national, domaine public, domaine privé : les catégories de terres au Sénégal": "COMPRENDRE",
    "Documents nécessaires pour immatriculer une parcelle": "IMMATRICULER",
    "Les étapes de la procédure d'immatriculation": "IMMATRICULER",
    "L'extrait de plan cadastral certifié": "IMMATRICULER",
    "Comment la valeur vénale est-elle estimée ?": "FISCALITE",
    "Comment la taxe foncière est-elle calculée ?": "FISCALITE",
    "La taxe foncière, dans la réalité sénégalaise": "FISCALITE",
    "Régler sa fiscalité foncière en ligne : les téléservices de la DGID": "FISCALITE",
    "Documents pour être à jour avec la fiscalité foncière": "FISCALITE",
    "Checklist : êtes-vous en règle ?": "PRATIQUE",
    "Questions fréquentes": "PRATIQUE",
    "Glossaire": "PRATIQUE",
}


def classer_sections(apps, schema_editor):
    SectionGuide = apps.get_model("core", "SectionGuide")
    for titre, categorie in CATEGORIES_PAR_TITRE.items():
        SectionGuide.objects.filter(titre=titre).update(categorie=categorie)


def revenir_en_arriere(apps, schema_editor):
    # Le champ lui-même est retiré par la migration précédente en cas de
    # "migrate" arrière ; rien à défaire ici.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_sectionguide_categorie"),
    ]

    operations = [
        migrations.RunPython(classer_sections, revenir_en_arriere),
    ]

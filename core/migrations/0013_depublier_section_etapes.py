from django.db import migrations

TITRE = "Les étapes de la procédure d'immatriculation"


def depublier(apps, schema_editor):
    SectionGuide = apps.get_model("core", "SectionGuide")
    SectionGuide.objects.filter(titre=TITRE).update(publie=False)


def republier(apps, schema_editor):
    SectionGuide = apps.get_model("core", "SectionGuide")
    SectionGuide.objects.filter(titre=TITRE).update(publie=True)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_backfill_categorie_sections"),
    ]

    operations = [
        migrations.RunPython(depublier, republier),
    ]

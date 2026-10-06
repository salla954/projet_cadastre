from django.db import migrations


def remapper_reclamation(apps, schema_editor):
    Dossier = apps.get_model("demarches", "Dossier")
    Dossier.objects.filter(type_dossier="RECLAMATION").update(type_dossier="RECLAMATION_FISCALE")


def revenir_en_arriere(apps, schema_editor):
    Dossier = apps.get_model("demarches", "Dossier")
    Dossier.objects.filter(type_dossier="RECLAMATION_FISCALE").update(type_dossier="RECLAMATION")


class Migration(migrations.Migration):

    dependencies = [
        ("demarches", "0002_alter_dossier_type_dossier"),
    ]

    operations = [
        migrations.RunPython(remapper_reclamation, revenir_en_arriere),
    ]

import random
import string

from django.db import migrations, models


def generer_reference_quittance(annee):
    suffixe = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"QUIT-{annee}-{suffixe}"


def remplir_references_existantes(apps, schema_editor):
    """Attribue une référence de quittance unique à chaque paiement déjà
    enregistré en base (ex. via l'import de la zone de Nguinth), avant que
    le champ ne devienne obligatoire et unique à l'étape suivante."""
    Paiement = apps.get_model("fiscalite", "Paiement")
    references_utilisees = set()
    for paiement in Paiement.objects.all():
        annee = paiement.date_paiement.year if paiement.date_paiement else 2026
        reference = generer_reference_quittance(annee)
        while reference in references_utilisees or Paiement.objects.filter(
            reference_quittance=reference
        ).exists():
            reference = generer_reference_quittance(annee)
        references_utilisees.add(reference)
        paiement.reference_quittance = reference
        paiement.save(update_fields=["reference_quittance"])


def revenir_en_arriere(apps, schema_editor):
    pass  # rien à défaire : le champ lui-même est retiré par la migration inverse.


class Migration(migrations.Migration):

    dependencies = [
        ("fiscalite", "0001_initial"),
    ]

    operations = [
        # 1) Ajout du champ, non unique pour l'instant (des lignes existantes
        #    partageraient sinon la même valeur vide, ce qui violerait la
        #    contrainte d'unicité ajoutée à l'étape 3).
        migrations.AddField(
            model_name="paiement",
            name="reference_quittance",
            field=models.CharField(
                "Référence de quittance", max_length=20, blank=True, default="", editable=False,
            ),
            preserve_default=False,
        ),
        # 2) Remplissage d'une référence unique pour chaque paiement déjà existant.
        migrations.RunPython(remplir_references_existantes, revenir_en_arriere),
        # 3) La contrainte d'unicité peut maintenant être ajoutée sans risque.
        migrations.AlterField(
            model_name="paiement",
            name="reference_quittance",
            field=models.CharField(
                "Référence de quittance", max_length=20, unique=True, blank=True, editable=False,
            ),
        ),
    ]

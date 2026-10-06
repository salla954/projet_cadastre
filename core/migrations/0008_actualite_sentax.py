import datetime

from django.db import migrations

ACTUALITES = [
    {
        "titre": "SENTAX remplace ETAX pour les grandes entreprises à partir de septembre 2026",
        "chapo": (
            "La DGID annonce que les contribuables relevant de la Direction des "
            "Grandes Entreprises (DGE) doivent désormais télédéclarer et "
            "télépayer via la nouvelle plateforme SENTAX, en lieu et place d'ETAX."
        ),
        "contenu": (
            "Depuis le 1er septembre 2026, la Direction générale des Impôts et "
            "des Domaines (DGID) impose l'utilisation de SENTAX pour l'ensemble "
            "des déclarations et paiements des contribuables suivis par la "
            "Direction des Grandes Entreprises (DGE) : les déclarations papier "
            "ne sont plus recevables pour ces usagers. L'accès au nouvel espace "
            "contribuable suppose une adhésion préalable sur sentax.dgid.sn, "
            "et la DGID invite les entreprises concernées à activer leur compte "
            "sans attendre la dernière minute.\n\n"
            "Ce basculement s'inscrit dans la continuité des précédents "
            "chantiers de dématérialisation de la DGID (ETAX, Mon Espace Perso, "
            "SenTimbre) : à terme, la plupart des démarches fiscales devraient "
            "être accessibles en ligne, sans déplacement dans un centre des "
            "services fiscaux."
        ),
        "date_publication": datetime.datetime(2026, 9, 2, 9, 0, tzinfo=datetime.timezone.utc),
        "source_url": "https://www.dgid.sn/sentax/",
    },
]


def creer_actualites(apps, schema_editor):
    Actualite = apps.get_model("core", "Actualite")
    for donnees in ACTUALITES:
        Actualite.objects.update_or_create(
            titre=donnees["titre"],
            defaults={
                "chapo": donnees["chapo"],
                "contenu": donnees["contenu"],
                "date_publication": donnees["date_publication"],
                "source_url": donnees.get("source_url", ""),
                "publie": True,
            },
        )


def supprimer_actualites(apps, schema_editor):
    Actualite = apps.get_model("core", "Actualite")
    titres = [donnees["titre"] for donnees in ACTUALITES]
    Actualite.objects.filter(titre__in=titres).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_seed_sections_dgid"),
    ]

    operations = [
        migrations.RunPython(creer_actualites, supprimer_actualites),
    ]

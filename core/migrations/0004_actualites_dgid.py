import datetime

from django.db import migrations

ACTUALITES = [
    {
        "titre": "SenTimbre : votre timbre fiscal en quelques clics, où que vous soyez",
        "chapo": (
            "La DGID présente SenTimbre, un service qui permet d'obtenir son "
            "timbre fiscal directement en ligne, sans passer par un guichet physique."
        ),
        "contenu": (
            "Grâce à l'application SenTimbre, les usagers peuvent désormais acheter "
            "leur timbre fiscal directement depuis leur téléphone, sans se déplacer "
            "dans un centre des services fiscaux. Le service est accessible 24h/24 "
            "et vise à simplifier les démarches liées aux actes soumis au droit de timbre."
        ),
        "date_publication": datetime.datetime(2026, 7, 22, 9, 0, tzinfo=datetime.timezone.utc),
        "source_url": "https://www.dgid.sn/2026/07/22/sentimbre-timbre-fiscal-en-ligne/",
    },
    {
        "titre": "Lancement de « SenTimbre »",
        "chapo": (
            "La Direction générale des Impôts et des Domaines annonce le lancement "
            "officiel de l'application SenTimbre, destinée à dématérialiser l'achat "
            "du timbre fiscal."
        ),
        "contenu": (
            "La DGID annonce la mise à disposition de SenTimbre, une application "
            "mobile permettant l'achat dématérialisé du timbre fiscal. Elle s'inscrit "
            "dans la continuité des efforts de digitalisation des services aux "
            "usagers menés par la DGID."
        ),
        "date_publication": datetime.datetime(2026, 7, 17, 10, 0, tzinfo=datetime.timezone.utc),
        "source_url": "https://www.dgid.sn/2026/07/17/lancement-de-sentimbre/",
    },
    {
        "titre": "Mise en service du paiement en ligne dans l'application « Mon Espace Perso » (MEP)",
        "chapo": (
            "La DGID informe les usagers de l'ouverture du paiement en ligne au "
            "sein de l'application Mon Espace Perso, facilitant le règlement des "
            "impôts à distance."
        ),
        "contenu": (
            "La DGID informe les usagers de l'ouverture d'un module de paiement en "
            "ligne au sein de l'application Mon Espace Perso (MEP). Les contribuables "
            "peuvent désormais régler leurs impôts directement depuis leur espace "
            "personnel, sans passer par un guichet."
        ),
        "date_publication": datetime.datetime(2026, 7, 17, 9, 0, tzinfo=datetime.timezone.utc),
        "source_url": "https://www.dgid.sn/2026/07/17/mise-en-service-du-paiement-en-ligne-dans-lapplication-mon-espace-perso-mep/",
    },
    {
        "titre": "Rappel du paiement du solde de l'Impôt sur le Revenu (IR) et de l'Impôt sur les Sociétés (IS)",
        "chapo": (
            "La DGID rappelle aux contribuables la date limite de paiement du "
            "solde de l'IR et de l'IS au titre de l'exercice en cours."
        ),
        "contenu": (
            "La DGID rappelle aux contribuables que le solde de l'Impôt sur le "
            "Revenu (IR) et de l'Impôt sur les Sociétés (IS) doit être réglé avant "
            "la date limite fixée par la réglementation fiscale en vigueur. Un "
            "retard de paiement expose le contribuable à des pénalités."
        ),
        "date_publication": datetime.datetime(2026, 6, 5, 9, 0, tzinfo=datetime.timezone.utc),
        "source_url": "https://www.dgid.sn/2026/06/05/solde-impot-revenu-is-2026/",
    },
    {
        "titre": "Journée de Réflexion et de Partage 2026 : la DGID engage son plan d'action",
        "chapo": (
            "Réunie le 11 mai 2026, la DGID a présenté les grandes orientations "
            "stratégiques de son plan d'action pour les mois à venir."
        ),
        "contenu": (
            "Le 11 mai 2026, la Direction générale des Impôts et des Domaines a "
            "tenu sa Journée de Réflexion et de Partage, réunissant l'ensemble du "
            "top management autour des orientations stratégiques de l'administration "
            "fiscale pour les mois à venir."
        ),
        "date_publication": datetime.datetime(2026, 5, 12, 9, 0, tzinfo=datetime.timezone.utc),
        "source_url": "https://www.dgid.sn/fiscalite/",
    },
    {
        "titre": "Rappel relatif aux modalités de règlement du deuxième acompte IR/IS",
        "chapo": (
            "La Direction du Recouvrement précise les modalités et l'échéance de "
            "règlement du deuxième acompte d'impôt, conformément au Code général "
            "des Impôts."
        ),
        "contenu": (
            "La Direction du Recouvrement rappelle aux contribuables que le "
            "règlement du deuxième acompte d'Impôt sur le Revenu et d'Impôt sur "
            "les Sociétés doit intervenir au plus tard le 30 avril, conformément "
            "aux articles 214 et 216 du Code général des Impôts. Le paiement dans "
            "les délais permet d'éviter les pénalités de retard."
        ),
        "date_publication": datetime.datetime(2026, 4, 30, 9, 0, tzinfo=datetime.timezone.utc),
        "source_url": "https://www.dgid.sn/fiscalite/",
    },
    {
        "titre": "Charte des droits et obligations du contribuable vérifié",
        "chapo": (
            "La DGID publie la charte rappelant les droits et obligations du "
            "contribuable faisant l'objet d'une vérification fiscale, conformément "
            "à la loi n° 2012-31."
        ),
        "contenu": (
            "Conformément à l'article 586-I de la loi n° 2012-31 du 31 décembre "
            "2012, la DGID publie une charte détaillant les droits et obligations "
            "du contribuable faisant l'objet d'une vérification fiscale, dans un "
            "souci de transparence et de sécurité juridique."
        ),
        "date_publication": datetime.datetime(2026, 2, 23, 9, 0, tzinfo=datetime.timezone.utc),
        "source_url": "https://www.dgid.sn/2026/02/23/",
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
        ("core", "0003_actualite_source_url"),
    ]

    operations = [
        migrations.RunPython(creer_actualites, supprimer_actualites),
    ]

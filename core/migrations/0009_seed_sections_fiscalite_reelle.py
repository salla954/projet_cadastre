from django.db import migrations

SECTIONS = [
    {
        "titre": "La taxe foncière, dans la réalité sénégalaise",
        "ordre": 65,
        "contenu": (
            "Le modèle de taxe foncière présenté sur cette plateforme est volontairement "
            "simplifié à des fins pédagogiques (un taux unique par usage, appliqué à une "
            "valeur vénale). Dans la réalité, la fiscalité foncière sénégalaise distingue "
            "deux impositions distinctes.\n\n"
            "- La Contribution Foncière des Propriétés Bâties (CFPB) concerne les "
            "constructions fixées au sol à perpétuelle demeure : maisons, bureaux, "
            "usines, entrepôts. Sa base n'est pas la valeur vénale mais la valeur "
            "locative annuelle du bien au 1er janvier de l'année d'imposition, avec un "
            "taux généralement fixé à 5 %.\n"
            "- La Contribution Foncière des Propriétés Non Bâties (CFPNB) s'applique aux "
            "terrains immatriculés qui ne portent aucune construction achevée (terrains "
            "de chantier, dépôts de marchandises, terrains en cours de construction, "
            "par exemple).\n\n"
            "Les propriétaires peuvent, sous conditions, demander une exonération "
            "temporaire (généralement cinq ans) pour une construction neuve, en "
            "déposant un dossier — demande, autorisation de construire, plans "
            "approuvés, certificat de conformité, titre de propriété — dans les quatre "
            "mois suivant l'ouverture des travaux. Un avis d'imposition à la CFPB peut "
            "également être rattaché à la taxe d'enlèvement des ordures ménagères "
            "(TEOM), facturée avec elle. Ces démarches relèvent du centre des services "
            "fiscaux territorialement compétent."
        ),
    },
    {
        "titre": "Régler sa fiscalité foncière en ligne : les téléservices de la DGID",
        "ordre": 66,
        "contenu": (
            "Au-delà du paiement au guichet, la Direction Générale des Impôts et des "
            "Domaines développe depuis plusieurs années des services numériques pour "
            "éviter aux contribuables de se déplacer.\n\n"
            "- Mon Espace Perso (MEP) : réservé aux particuliers et aux entreprises dont "
            "le chiffre d'affaires ne dépasse pas 100 millions de FCFA, il permet de "
            "consulter son dossier fiscal, ses comptes d'impôts et d'échanger "
            "directement avec son agent fiscal.\n"
            "- ETAX, puis SENTAX : ces applications permettent de télédéclarer et de "
            "télépayer ses impôts et taxes avec un identifiant et un mot de passe "
            "délivrés par l'administration. Depuis septembre 2026, SENTAX est devenu "
            "obligatoire pour les contribuables suivis par la Direction des Grandes "
            "Entreprises.\n"
            "- DGID-digitale : facilite l'obtention de documents comme le quitus "
            "fiscal ou l'attestation d'imposition/de non-imposition.\n\n"
            "Cette plateforme de démonstration ne reproduit pas ces téléservices, mais "
            "s'en inspire : le suivi du montant dû, payé et restant pour chaque taxe, "
            "ainsi que le téléchargement d'un extrait de plan, vont dans le même sens "
            "— simplifier le lien entre l'administration et l'usager."
        ),
    },
]


def creer_sections(apps, schema_editor):
    SectionGuide = apps.get_model("core", "SectionGuide")
    for donnees in SECTIONS:
        SectionGuide.objects.update_or_create(
            titre=donnees["titre"],
            defaults={"contenu": donnees["contenu"], "ordre": donnees["ordre"], "publie": True},
        )


def supprimer_sections(apps, schema_editor):
    SectionGuide = apps.get_model("core", "SectionGuide")
    titres = [donnees["titre"] for donnees in SECTIONS]
    SectionGuide.objects.filter(titre__in=titres).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_actualite_sentax"),
    ]

    operations = [
        migrations.RunPython(creer_sections, supprimer_sections),
    ]

from django.db import migrations

SECTIONS = [
    {
        "titre": "Qu'est-ce que le NICAD ?",
        "ordre": 15,
        "contenu": (
            "Le NICAD (Numéro d'Identification Cadastrale) est un identifiant unique et obligatoire "
            "attribué à chaque parcelle de terrain au Sénégal, quel que soit son statut juridique. "
            "Institué par le décret n° 2012-396 du 27 mars 2012, il met fin à la juxtaposition "
            "d'anciens systèmes de repérage (numéro de titre foncier, numéro de lot, référence de "
            "bail) qui entretenait confusion et litiges.\n\n"
            "Le NICAD est délivré gratuitement par le bureau du cadastre territorialement compétent, "
            "sous la forme d'un Certificat d'Identification Cadastrale (CIC), généralement dans un "
            "délai de 5 jours ouvrés. Ce certificat reste valable 6 mois.\n\n"
            "Un point important à retenir : le NICAD n'est pas la même chose que le titre foncier. "
            "Une parcelle peut très bien avoir un NICAD sans être encore immatriculée (par exemple un "
            "terrain du domaine national ou une parcelle dont la procédure d'immatriculation est en "
            "cours). En revanche, tout titre foncier délivré aujourd'hui doit obligatoirement être "
            "associé à un NICAD."
        ),
    },
    {
        "titre": "Domaine national, domaine public, domaine privé : les catégories de terres au Sénégal",
        "ordre": 25,
        "contenu": (
            "Toutes les terres du Sénégal ne relèvent pas du même régime juridique. On distingue "
            "principalement trois grandes catégories.\n\n"
            "Le domaine national regroupe les terres non classées dans le domaine public et non "
            "encore immatriculées au nom d'un propriétaire privé. Institué par la loi n° 64-46 du 17 "
            "juin 1964, il représentait à l'origine plus de 95 % du territoire sénégalais. C'est "
            "notamment sur ces terres que s'engagent la plupart des démarches d'immatriculation "
            "décrites dans ce guide.\n\n"
            "Le domaine public de l'État regroupe les biens qui, par leur nature ou leur destination, "
            "ne peuvent pas faire l'objet d'une appropriation privée : la mer territoriale, les cours "
            "d'eau navigables, les routes, par exemple. Ces biens sont inaliénables, insaisissables et "
            "imprescriptibles.\n\n"
            "Le domaine privé de l'État, à l'inverse, regroupe des biens qui peuvent être cédés ou "
            "attribués à des particuliers (réserves foncières de l'État, par exemple).\n\n"
            "Une fois qu'une parcelle est immatriculée, elle devient une propriété privée à part "
            "entière, opposable à tous : c'est tout l'objet de la procédure d'immatriculation "
            "présentée plus haut dans ce guide."
        ),
    },
    {
        "titre": "L'extrait de plan cadastral certifié",
        "ordre": 45,
        "contenu": (
            "L'extrait de plan cadastral certifié est un document officiel qui représente "
            "graphiquement une parcelle sur le plan cadastral national : ses limites, sa superficie, "
            "son numéro de parcelle et sa localisation dans la section cadastrale concernée. La "
            "mention « certifié » signifie que le document est authentifié par le chef d'inspection "
            "du cadastre territorialement compétent, ce qui lui donne une valeur juridique opposable "
            "aux tiers.\n\n"
            "Ce document est notamment exigé pour constituer un dossier de bail, d'immatriculation, "
            "d'autorisation de construire ou de morcellement d'une parcelle. Il est étroitement lié "
            "au NICAD, puisqu'il en constitue l'une des pièces justificatives.\n\n"
            "À noter : l'aperçu de plan que vous pouvez télécharger depuis cette plateforme pour "
            "chaque parcelle est une représentation à but démonstratif, générée à partir des données "
            "enregistrées ici. Il ne remplace pas l'extrait de plan cadastral certifié délivré par le "
            "bureau du cadastre, seul document ayant une valeur juridique officielle."
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
        ("core", "0006_seed_sections_guide"),
    ]

    operations = [
        migrations.RunPython(creer_sections, supprimer_sections),
    ]

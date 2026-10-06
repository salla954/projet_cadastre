from django.db import migrations

TITRE_EXTRAIT = "L'extrait de plan cadastral certifié"
CONTENU_EXTRAIT = (
    "L'extrait de plan cadastral certifié est un document officiel qui représente "
    "graphiquement une parcelle sur le plan cadastral national : ses limites, sa superficie, "
    "son numéro de parcelle et sa localisation dans la section cadastrale concernée. La "
    "mention « certifié » signifie que le document est authentifié par le chef d'inspection "
    "du cadastre territorialement compétent, ce qui lui donne une valeur juridique opposable "
    "aux tiers.\n\n"
    "Ce document est notamment exigé pour constituer un dossier de bail, d'immatriculation, "
    "d'autorisation de construire ou de morcellement d'une parcelle. Il est étroitement lié "
    "au NICAD, puisqu'il en constitue l'une des pièces justificatives.\n\n"
    "À noter : sur cette plateforme, l'aperçu de plan associé à chaque parcelle n'est pas "
    "téléchargeable directement par l'usager — il est généré par un agent du cadastre, "
    "notamment lors du traitement d'une demande d'« Extrait cadastral » déposée en ligne. "
    "Il s'agit d'une représentation à but démonstratif, générée à partir des données "
    "enregistrées ici, et qui ne remplace pas l'extrait de plan cadastral certifié délivré "
    "par le bureau du cadastre, seul document ayant une valeur juridique officielle."
)

TITRE_TELESERVICES = "Régler sa fiscalité foncière en ligne : les téléservices de la DGID"
ANCIEN_FRAGMENT = (
    "Cette plateforme de démonstration ne reproduit pas ces téléservices, mais "
    "s'en inspire : le suivi du montant dû, payé et restant pour chaque taxe, "
    "ainsi que le téléchargement d'un extrait de plan, vont dans le même sens "
    "— simplifier le lien entre l'administration et l'usager."
)
NOUVEAU_FRAGMENT = (
    "Cette plateforme de démonstration ne reproduit pas ces téléservices, mais "
    "s'en inspire : le suivi du montant dû, payé et restant pour chaque taxe, "
    "ainsi que le dépôt en ligne d'une demande d'extrait cadastral (ensuite "
    "traitée par un agent), vont dans le même sens — simplifier le lien entre "
    "l'administration et l'usager."
)


def corriger_textes(apps, schema_editor):
    SectionGuide = apps.get_model("core", "SectionGuide")
    SectionGuide.objects.filter(titre=TITRE_EXTRAIT).update(contenu=CONTENU_EXTRAIT)
    # RunPython ne peut pas faire un remplacement de sous-chaîne via l'ORM
    # directement : on relit puis on réécrit la valeur en Python.
    for section in SectionGuide.objects.filter(titre=TITRE_TELESERVICES):
        if ANCIEN_FRAGMENT in section.contenu:
            section.contenu = section.contenu.replace(ANCIEN_FRAGMENT, NOUVEAU_FRAGMENT)
            section.save(update_fields=["contenu"])


def revenir_en_arriere(apps, schema_editor):
    SectionGuide = apps.get_model("core", "SectionGuide")
    for section in SectionGuide.objects.filter(titre=TITRE_TELESERVICES):
        if NOUVEAU_FRAGMENT in section.contenu:
            section.contenu = section.contenu.replace(NOUVEAU_FRAGMENT, ANCIEN_FRAGMENT)
            section.save(update_fields=["contenu"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_depublier_section_etapes"),
    ]

    operations = [
        migrations.RunPython(corriger_textes, revenir_en_arriere),
    ]

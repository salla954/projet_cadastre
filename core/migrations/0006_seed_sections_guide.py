from django.db import migrations

SECTIONS = [
    {
        "titre": "Qu'est-ce que le cadastre ?",
        "ordre": 10,
        "contenu": (
            "Le cadastre est l'inventaire officiel des parcelles de terrain d'un territoire. Pour "
            "chaque parcelle, il enregistre sa référence cadastrale (son identifiant unique), sa "
            "localisation, sa superficie, ainsi que l'identité de son ou ses propriétaires. Il sert "
            "de base légale et technique à toute décision liée au foncier : vente, héritage, "
            "construction ou imposition.\n\n"
            "Trois éléments clés à retenir :\n"
            "- Référence cadastrale : un code unique attribué à chaque parcelle, qui permet de la "
            "retrouver instantanément dans la base de données.\n"
            "- Superficie : la surface exacte de la parcelle, mesurée en mètres carrés, qui sert "
            "notamment au calcul de sa valeur.\n"
            "- Propriétaire : la ou les personnes reconnues comme détentrices légales de la parcelle "
            "auprès des services du cadastre."
        ),
    },
    {
        "titre": "Qu'est-ce que l'immatriculation ?",
        "ordre": 20,
        "contenu": (
            "Immatriculer une parcelle, c'est l'inscrire officiellement au cadastre et lui délivrer "
            "un titre foncier. Une parcelle immatriculée est juridiquement sécurisée : son "
            "propriétaire est clairement identifié et ses droits sont opposables à tous. Une parcelle "
            "non immatriculée peut faire l'objet de litiges de propriété et n'est pas encore reconnue "
            "dans le système fiscal officiel.\n\n"
            "Sur la plateforme, chaque parcelle affiche l'un de ces statuts :\n"
            "- Immatriculée : la parcelle possède un titre foncier et figure dans le registre "
            "officiel. Elle peut être vendue, hypothéquée ou transmise en toute sécurité.\n"
            "- En cours d'immatriculation : la procédure a été engagée (bornage ou publication en "
            "cours) mais n'est pas finalisée. [Suivre l'avancement](/demarches/suivre/) de votre "
            "dossier ; patienter le délai d'opposition.\n"
            "- Non immatriculée : aucune démarche d'inscription n'a encore été effectuée. "
            "[Déposer une réquisition d'immatriculation](/demarches/deposer/)."
        ),
    },
    {
        "titre": "Documents nécessaires pour immatriculer une parcelle",
        "ordre": 30,
        "contenu": (
            "Pour engager ou finaliser l'immatriculation d'une parcelle, les documents suivants sont "
            "généralement demandés par le service du cadastre. La liste exacte peut varier selon la "
            "situation (achat, héritage, terrain communal) ; il est conseillé de la confirmer auprès "
            "du bureau du cadastre de votre commune.\n\n"
            "- Réquisition d'immatriculation : formulaire officiel qui ouvre la procédure auprès du "
            "service du cadastre.\n"
            "- Pièce d'identité du demandeur : justifie l'identité du propriétaire déclaré.\n"
            "- Justificatif de propriété ou d'occupation : acte de vente, attestation d'attribution, "
            "acte de succession ou délibération municipale.\n"
            "- Plan de bornage / plan géométrique : localise précisément les limites de la parcelle, "
            "établi par un géomètre agréé.\n"
            "- Certificat de non-opposition/non-litige : atteste qu'aucune contestation n'existe sur "
            "la parcelle au moment de la demande.\n"
            "- Quittances des impôts fonciers antérieurs : prouve que la fiscalité déjà due sur le "
            "terrain est à jour (le cas échéant).\n"
            "- Photos ou constat de mise en valeur : justifie l'usage effectif de la parcelle "
            "(habitation, culture, construction).\n\n"
            "Bon à savoir : conservez toujours une copie de chaque document déposé et demandez un "
            "récépissé de dépôt : il fait foi en cas de besoin pendant l'instruction du dossier."
        ),
    },
    {
        "titre": "Les étapes de la procédure d'immatriculation",
        "ordre": 40,
        "contenu": (
            "Une fois le dossier déposé, la parcelle suit un parcours précis avant de recevoir son "
            "titre foncier. Le plan de bornage, réalisé par un géomètre, en est une étape centrale : "
            "il fixe juridiquement les limites exactes du terrain.\n\n"
            "1. Dépôt de la demande : la réquisition d'immatriculation et les pièces justificatives "
            "sont déposées auprès du service du cadastre. [Déposer mon dossier en ligne](/demarches/deposer/).\n"
            "2. Bornage du terrain : un géomètre matérialise les limites exactes de la parcelle et "
            "établit le plan cadastral correspondant.\n"
            "3. Publication et opposition : la demande est publiée pour permettre à d'éventuels tiers "
            "de faire valoir leurs droits pendant un délai légal.\n"
            "4. Instruction du dossier : en l'absence d'opposition recevable, le service du cadastre "
            "examine et valide le dossier complet.\n"
            "5. Délivrance du titre foncier : la parcelle est inscrite au livre foncier et le titre "
            "foncier est remis au propriétaire.\n"
            "6. Mise à jour sur la plateforme : le statut de la parcelle passe à « Immatriculée » et "
            "devient consultable publiquement par référence."
        ),
    },
    {
        "titre": "Comment la valeur vénale est-elle estimée ?",
        "ordre": 50,
        "contenu": (
            "La valeur vénale correspond au prix auquel une parcelle pourrait raisonnablement se "
            "vendre sur le marché à un moment donné. Elle est estimée en tenant compte principalement "
            "de :\n\n"
            "- la localisation de la parcelle (commune, quartier, proximité des axes) ;\n"
            "- sa superficie ;\n"
            "- l'usage du terrain (habitation, commerce, agriculture) ;\n"
            "- les prix pratiqués sur des parcelles comparables dans la même zone.\n\n"
            "Cette valeur, une fois déterminée, devient la référence sur laquelle repose le calcul de "
            "la taxe foncière."
        ),
    },
    {
        "titre": "Comment la taxe foncière est-elle calculée ?",
        "ordre": 60,
        "contenu": (
            "La taxe foncière est l'impôt annuel dû par le propriétaire d'une parcelle immatriculée. "
            "Elle est calculée en appliquant un taux d'imposition à la valeur vénale de la parcelle :\n\n"
            "- Valeur vénale : base de calcul de l'impôt (montant estimé de la parcelle).\n"
            "- Taux d'imposition : pourcentage fixé par la réglementation en vigueur.\n"
            "- Montant dû : valeur vénale × taux d'imposition = taxe foncière annuelle.\n\n"
            "Une fois l'avis de taxe émis, le propriétaire peut effectuer son paiement en une ou "
            "plusieurs fois. La plateforme permet de suivre à tout moment le montant dû, le montant "
            "déjà payé et le solde restant."
        ),
    },
    {
        "titre": "Documents pour être à jour avec la fiscalité foncière",
        "ordre": 70,
        "contenu": (
            "Une fois la parcelle immatriculée, rester « en règle » consiste surtout à suivre et "
            "conserver les documents liés au paiement de l'impôt foncier, année après année.\n\n"
            "- Avis de taxe foncière : notifie chaque année le montant dû pour la parcelle concernée.\n"
            "- Quittance / reçu de paiement : preuve officielle qu'un paiement a bien été effectué, à "
            "conserver précieusement.\n"
            "- Certificat de non-redevance : atteste qu'aucune taxe foncière n'est due sur la "
            "parcelle, souvent exigé pour une vente.\n"
            "- Relevé de situation fiscale : récapitule l'historique des montants dus et payés sur "
            "plusieurs années.\n\n"
            "Astuce : le statut de paiement (à jour, partiel, en retard) de chaque parcelle est "
            "visible directement via la [consultation publique](/accueil/consultation/)."
        ),
    },
    {
        "titre": "Checklist : êtes-vous en règle ?",
        "ordre": 80,
        "contenu": (
            "Pour être pleinement en règle vis-à-vis du cadastre et de la fiscalité foncière, "
            "vérifiez que vous disposez de :\n\n"
            "- Un titre foncier : la parcelle est immatriculée et apparaît avec le statut « "
            "Immatriculée » sur la plateforme.\n"
            "- Un plan de bornage à jour : les limites de la parcelle correspondent bien à celles "
            "enregistrées au cadastre.\n"
            "- Vos avis de taxe réglés : aucun solde restant dû sur les années précédentes, "
            "vérifiable via la consultation publique.\n"
            "- Vos quittances conservées : chaque paiement de taxe foncière est justifié par une "
            "quittance gardée en lieu sûr."
        ),
    },
    {
        "titre": "Questions fréquentes",
        "ordre": 90,
        "contenu": (
            "Ma parcelle n'est pas encore immatriculée, est-ce grave ?\n"
            "Ce n'est pas une infraction en soi, mais cela expose à des litiges de propriété et "
            "empêche la reconnaissance officielle de vos droits. Il est recommandé d'engager la "
            "procédure d'immatriculation dès que possible.\n\n"
            "Que se passe-t-il si je ne paie pas ma taxe foncière ?\n"
            "Le solde impayé reste dû et s'accumule d'une année sur l'autre. Il peut compliquer une "
            "future vente ou démarche administrative, un certificat de non-redevance étant souvent "
            "exigé.\n\n"
            "Où déposer mon dossier d'immatriculation ?\n"
            "Directement en ligne via la page [Déposer un dossier](/demarches/deposer/), ou auprès du "
            "service du cadastre compétent pour la commune où se trouve la parcelle. Une référence de "
            "suivi vous est remise, à utiliser sur la page [Suivre un dossier](/demarches/suivre/) "
            "pour connaître son état d'avancement.\n\n"
            "Comment connaître le statut exact de ma parcelle ?\n"
            "Utilisez la [consultation publique](/accueil/consultation/) et recherchez votre parcelle "
            "par sa référence cadastrale : statut d'immatriculation et situation fiscale s'affichent "
            "instantanément."
        ),
    },
    {
        "titre": "Glossaire",
        "ordre": 100,
        "contenu": (
            "Cadastre : inventaire officiel des parcelles d'un territoire.\n"
            "Référence cadastrale : identifiant unique attribué à chaque parcelle.\n"
            "Immatriculation : inscription officielle d'une parcelle au registre foncier.\n"
            "Titre foncier : document juridique qui reconnaît et protège la propriété d'une parcelle "
            "immatriculée.\n"
            "Bornage : opération technique qui matérialise les limites exactes d'une parcelle.\n"
            "Valeur vénale : estimation du prix de vente d'une parcelle sur le marché.\n"
            "Taxe foncière : impôt annuel dû par le propriétaire d'une parcelle immatriculée.\n"
            "Certificat de non-redevance : document attestant qu'aucune taxe foncière n'est due sur "
            "une parcelle."
        ),
    },
]


def creer_sections(apps, schema_editor):
    SectionGuide = apps.get_model("core", "SectionGuide")
    for donnees in SECTIONS:
        SectionGuide.objects.get_or_create(
            titre=donnees["titre"],
            defaults={"contenu": donnees["contenu"], "ordre": donnees["ordre"], "publie": True},
        )


def supprimer_sections(apps, schema_editor):
    SectionGuide = apps.get_model("core", "SectionGuide")
    titres = [donnees["titre"] for donnees in SECTIONS]
    SectionGuide.objects.filter(titre__in=titres).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_sectionguide"),
    ]

    operations = [
        migrations.RunPython(creer_sections, supprimer_sections),
    ]

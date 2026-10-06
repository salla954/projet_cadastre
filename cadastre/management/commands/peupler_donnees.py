import random
from datetime import date

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker

from cadastre.models import Commune, Proprietaire, Parcelle
from fiscalite.models import TaxeFonciere, Paiement
from core.models import Actualite
from demarches.models import Dossier

fake = Faker("fr_FR")

# Utilisé uniquement pour générer un texte de localisation plausible sur les
# dossiers fictifs qui ne sont pas rattachés à une parcelle réelle (voir plus
# bas) — ce ne sont pas des communes créées en base : les seules parcelles et
# communes de cette plateforme proviennent de l'import de données réelles
# (voir la commande importer_bd_zone_nguinth).
NOMS_COMMUNES_THIES = [
    "Thiès Nord", "Thiès Est", "Thiès Ouest", "Mbour", "Tivaouane",
    "Khombole", "Pout", "Notto", "Meckhé", "Joal-Fadiouth",
]


class Command(BaseCommand):
    help = (
        "Peuple la base avec des actualités et des dossiers de démonstration. "
        "Les parcelles, communes et propriétaires ne sont plus générés ici : "
        "ils proviennent exclusivement de l'import de données réelles "
        "(voir la commande importer_bd_zone_nguinth)."
    )

    def handle(self, *args, **options):
        # Nettoyage de sécurité : si d'anciennes parcelles fictives, générées
        # par une version précédente de cette commande, traînent encore en
        # base, on les retire avec leurs taxes/paiements et les communes ou
        # propriétaires devenus orphelins — seules les parcelles importées
        # depuis une géométrie réelle (commune "Nguinth", voir
        # importer_bd_zone_nguinth) doivent subsister sur cette plateforme.
        parcelles_non_reelles = Parcelle.objects.exclude(commune__nom="Nguinth")
        nb_parcelles_retirees = parcelles_non_reelles.count()
        if nb_parcelles_retirees:
            Paiement.objects.filter(taxe__parcelle__in=parcelles_non_reelles).delete()
            TaxeFonciere.objects.filter(parcelle__in=parcelles_non_reelles).delete()
            parcelles_non_reelles.delete()
            Proprietaire.objects.filter(parcelles__isnull=True).delete()
            Commune.objects.exclude(nom="Nguinth").filter(parcelles__isnull=True).delete()
            self.stdout.write(
                f"{nb_parcelles_retirees} ancienne(s) parcelle(s) non réelle(s) retirée(s) "
                f"(données d'une précédente version de cette commande)."
            )

        self.stdout.write("Suppression des anciennes actualités et anciens dossiers de démonstration...")
        # On ne supprime que les actualités gérées par cette commande (sans
        # source_url). Les actualités institutionnelles réelles de la DGID,
        # elles, sont gérées par des migrations de données (voir
        # core/migrations/0004_actualites_dgid.py et suivantes) et ne doivent
        # pas être effacées à chaque re-génération des données fictives.
        Actualite.objects.filter(source_url="").delete()

        # --- Actualités ---
        titres = [
            ("Campagne de sensibilisation sur la taxe foncière 2026",
             "La direction du cadastre lance une campagne d'information dans les communes de la région."),
            ("Ouverture du guichet unique d'immatriculation à Thiès Nord",
             "Un nouveau guichet facilite les démarches d'immatriculation pour les propriétaires."),
            ("Mise à jour du plan cadastral de Mbour",
             "Le plan parcellaire de la commune de Mbour a été actualisé suite aux relevés topographiques."),
            ("Échéance de paiement de la taxe foncière 2025",
             "Les contribuables sont invités à régulariser leur situation avant le 31 décembre."),
        ]
        for titre, chapo in titres:
            Actualite.objects.create(
                titre=titre, chapo=chapo,
                contenu=chapo + " " + fake.paragraph(nb_sentences=6),
            )
        self.stdout.write("Actualités créées.")

        # --- Actualités institutionnelles ---
        # Articles rédigés à partir d'informations publiques (www.dgid.sn et
        # presse sénégalaise) sur de vrais programmes de la DGID, pour ancrer
        # la plateforme dans son contexte réel. Contenu original, à visée
        # pédagogique ; la plateforme et ses données restent 100% fictives.
        NOTE_SOURCE = (
            "\n\n⚠️ Article rédigé à titre pédagogique à partir d'informations "
            "publiques (www.dgid.sn et presse sénégalaise). Cette plateforme "
            "n'est affiliée à aucun des programmes cités ; ses données "
            "(parcelles, propriétaires, montants) restent entièrement fictives."
        )

        actualites_institutionnelles = [
            (
                "Le programme national Yaatal et l'élargissement de l'assiette fiscale",
                "Porté par la DGID depuis 2020, le programme Yaatal vise à recenser "
                "davantage de contribuables et à mieux valoriser le foncier : un "
                "contexte qui éclaire la vocation de cette plateforme locale.",
                "Le mot « Yaatal » signifie « élargir » en wolof. Lancé par la "
                "Direction générale des Impôts et des Domaines (DGID) dans le cadre "
                "de la Stratégie de mobilisation des recettes à moyen terme "
                "(SRMT 2020-2025), ce programme national poursuit un triple objectif : "
                "identifier les propriétés et leurs occupants, simplifier les "
                "démarches déclaratives, et croiser les informations déjà détenues "
                "par l'administration (permis de construire, actes notariés, "
                "factures d'eau et d'électricité) pour repérer les biens non "
                "déclarés. Son mot d'ordre, « Yaatal natt teggui yokkuté », invite "
                "chaque citoyen à contribuer à un développement partagé par le "
                "civisme fiscal.\n\n"
                "Pour une région comme Thiès, où de nombreuses parcelles restent "
                "encore non immatriculées ou insuffisamment valorisées sur le plan "
                "fiscal, cette dynamique nationale trouve un écho direct : recenser "
                "les parcelles, connaître leur statut d'immatriculation et suivre le "
                "paiement des taxes, c'est précisément la mission de cette "
                "plateforme démonstrative de cadastre et de fiscalité foncière."
                + NOTE_SOURCE,
            ),
            (
                "PROCASEF : la région de Thiès concernée par la sécurisation foncière rurale",
                "Le Projet cadastre et sécurisation foncière, financé par la Banque "
                "mondiale, inclut plusieurs communes de la zone Dakar-Thiès dans son "
                "dispositif de modernisation du cadastre.",
                "Piloté par le ministère des Finances et du Budget avec l'appui "
                "technique de la DGID, le Projet cadastre et sécurisation foncière "
                "(PROCASEF) est une initiative quinquennale (2021-2026) soutenue par "
                "un financement de la Banque mondiale d'environ 80 millions de "
                "dollars. Son objectif : sécuriser les droits fonciers dans les zones "
                "rurales et périurbaines d'une centaine de communes réparties sur le "
                "territoire, notamment en appuyant la délivrance de titres ou de "
                "certificats de propriété.\n\n"
                "Le projet est organisé en cinq grandes zones d'intervention, dont "
                "celle du Grand Dakar, qui regroupe une vingtaine de communes situées "
                "entre Dakar et la région de Thiès. Sur le terrain, les équipes du "
                "PROCASEF appuient les services du cadastre pour clarifier les "
                "limites des parcelles, recenser les occupants et alimenter un "
                "registre foncier numérique appelé à remplacer progressivement les "
                "archives papier — une dématérialisation dont la région de Thiès a "
                "d'ailleurs été l'une des premières bénéficiaires.\n\n"
                "Cet enjeu de traçabilité est aussi celui que cette plateforme "
                "cherche à représenter à petite échelle : une référence cadastrale "
                "unique et un statut d'immatriculation clair pour chaque parcelle."
                + NOTE_SOURCE,
            ),
            (
                "Pourquoi chaque parcelle a besoin d'une référence cadastrale unique",
                "Un décret de 2012 a instauré au Sénégal un numéro cadastral unique "
                "pour mettre fin aux confusions entre registres communaux et "
                "registres du cadastre — la même logique que la référence attribuée "
                "à chaque parcelle sur cette plateforme.",
                "Pendant longtemps, une même parcelle pouvait être suivie séparément "
                "par les services du cadastre et par les communes, sans lien réel "
                "entre les deux systèmes : il est arrivé que des mairies délibèrent "
                "sur des titres fonciers sans savoir qu'un dossier existait déjà au "
                "cadastre. Pour corriger ce défaut de coordination, un décret pris en "
                "mars 2012 a instauré un numéro cadastral unique, que l'ensemble des "
                "acteurs — cadastre, administration centrale et collectivités "
                "locales — doivent désormais utiliser pour identifier une parcelle "
                "donnée, en zone rurale comme dans le domaine national.\n\n"
                "Cette exigence de traçabilité est au cœur du fonctionnement de la "
                "plateforme : chaque parcelle enregistrée reçoit une référence "
                "cadastrale unique (par exemple TH-2024-00147), qui permet de "
                "retrouver instantanément sa localisation, son statut "
                "d'immatriculation et sa situation fiscale, depuis la consultation "
                "publique comme depuis le tableau de bord de l'agent."
                + NOTE_SOURCE,
            ),
            (
                "Taxe foncière : un potentiel de recettes encore largement sous-exploité",
                "En Afrique subsaharienne, la taxe foncière ne représente en moyenne "
                "que 2 % des recettes fiscales, contre près de 9 % dans les pays de "
                "l'OCDE — et une part encore plus faible au Sénégal.",
                "Depuis 2017, la DGID collabore avec des chercheurs spécialisés en "
                "fiscalité pour identifier les obstacles à une meilleure collecte de "
                "la taxe foncière au Sénégal. Plusieurs difficultés reviennent "
                "régulièrement : un cadastre souvent incomplet ou périmé, des "
                "déclarations spontanées de propriétaires rares, et un travail de "
                "terrain coûteux pour évaluer la valeur réelle des biens en "
                "l'absence de données fiables.\n\n"
                "Une taxe foncière bien recouvrée est pourtant une ressource stable "
                "pour financer les infrastructures locales (voirie, éclairage, "
                "écoles, marchés) sans dépendre uniquement des transferts de l'État. "
                "Améliorer le suivi des parcelles, connaître leur usage et leur "
                "valeur, et fluidifier le paiement des avis de taxe sont autant de "
                "leviers pour combler cet écart.\n\n"
                "C'est précisément l'ambition pédagogique de cette plateforme : "
                "montrer comment un système d'information cadastral et fiscal, même "
                "simplifié, peut donner à une commune une vision claire de son "
                "patrimoine foncier imposable."
                + NOTE_SOURCE,
            ),
        ]
        for titre, chapo, contenu in actualites_institutionnelles:
            Actualite.objects.create(titre=titre, chapo=chapo, contenu=contenu)
        self.stdout.write("Actualités institutionnelles (DGID) créées.")

        # --- Dossiers déposés (démarches) : données fictives ---
        Dossier.objects.all().delete()
        descriptions_par_type = {
            Dossier.IMMATRICULATION: "Demande d'immatriculation pour une parcelle à usage résidentiel.",
            Dossier.PLAN_SITUATION: "Demande d'un plan de situation pour localiser précisément la parcelle.",
            Dossier.EXTRAIT_CADASTRAL: "Demande d'extrait cadastral pour constituer un dossier de vente.",
            Dossier.RENSEIGNEMENT_PARCELLE: "Demande de renseignements sur la situation juridique de la parcelle.",
            Dossier.BORNAGE: "Demande de bornage contradictoire suite à un doute sur les limites du terrain.",
            Dossier.MORCELLEMENT: "Demande de morcellement d'une parcelle en plusieurs lots distincts.",
            Dossier.FUSION: "Demande de fusion de deux parcelles limitrophes appartenant au même propriétaire.",
            Dossier.MISE_A_JOUR_CADASTRALE: "Demande de mise à jour des informations cadastrales suite à une construction.",
            Dossier.SITUATION_FISCALE: "Demande de situation fiscale détaillée de la parcelle.",
            Dossier.ATTESTATION_FISCALE: "Demande d'attestation de non-redevance pour un dossier administratif.",
            Dossier.PAIEMENT_QUITTANCE: "Demande de duplicata de quittance suite à la perte de l'original.",
            Dossier.REGULARISATION_FISCALE: "Demande de régularisation d'arriérés de taxe foncière, avec échéancier.",
            Dossier.RECLAMATION_FISCALE: "Réclamation relative à une erreur constatée sur l'avis de taxe foncière.",
            Dossier.CONSULTATION_IMPOTS_DUS: "Demande de consultation du montant total des impôts fonciers dus.",
        }
        types_dossier = list(descriptions_par_type.keys())
        # Légère pondération : l'immatriculation et les demandes fiscales courantes
        # reviennent un peu plus souvent, comme dans la réalité.
        poids_types = {
            Dossier.IMMATRICULATION: 3, Dossier.SITUATION_FISCALE: 2,
            Dossier.RECLAMATION_FISCALE: 2, Dossier.PAIEMENT_QUITTANCE: 2,
        }
        types_ponderes = []
        for type_dossier in types_dossier:
            types_ponderes += [type_dossier] * poids_types.get(type_dossier, 1)

        statuts_dossier = [Dossier.DEPOSE, Dossier.EN_COURS, Dossier.EN_COURS, Dossier.VALIDE, Dossier.REJETE]
        # Parcelles réelles disponibles (import Nguinth) pour rattacher une
        # partie des dossiers fictifs à une vraie parcelle plutôt qu'à une
        # simple localisation saisie à la main.
        parcelles_reelles = list(Parcelle.objects.all()[:500])
        nb_dossiers = 0
        for _ in range(40):
            type_dossier = random.choice(types_ponderes)
            parcelle_liee = (
                random.choice(parcelles_reelles)
                if parcelles_reelles and random.random() < 0.6 else None
            )
            Dossier.objects.create(
                type_dossier=type_dossier,
                parcelle=parcelle_liee,
                localisation_saisie="" if parcelle_liee else f"{random.choice(NOMS_COMMUNES_THIES)}, {fake.street_name()}",
                nom_demandeur=fake.name(),
                telephone_demandeur=fake.phone_number(),
                email_demandeur=fake.email() if random.random() < 0.5 else "",
                description=descriptions_par_type[type_dossier],
                statut=random.choice(statuts_dossier),
            )
            nb_dossiers += 1
        self.stdout.write(f"{nb_dossiers} dossiers (démarches) créés.")

        # --- Utilisateur agent de démonstration ---
        if not User.objects.filter(username="agent").exists():
            User.objects.create_superuser("agent", "agent@example.sn", "CadastreThies2026!")
            self.stdout.write(self.style.SUCCESS(
                "Utilisateur créé -> identifiant : agent / mot de passe : CadastreThies2026!"
            ))

        self.stdout.write(self.style.SUCCESS("Peuplement terminé avec succès."))

import random
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker

from cadastre.models import Commune, Proprietaire, Parcelle
from fiscalite.models import TaxeFonciere, Paiement, TAUX_PAR_USAGE
from core.models import Actualite

fake = Faker("fr_FR")

COMMUNES_THIES = [
    ("Thiès Nord", 180000), ("Thiès Est", 165000), ("Thiès Ouest", 140000),
    ("Mbour", 250000), ("Tivaouane", 60000), ("Khombole", 35000),
    ("Pout", 28000), ("Notto", 22000), ("Meckhé", 40000), ("Joal-Fadiouth", 45000),
]

USAGES = ["RESIDENTIEL", "COMMERCIAL", "AGRICOLE", "INDUSTRIEL", "MIXTE"]
STATUTS = ["IMMATRICULEE", "IMMATRICULEE", "EN_COURS", "LITIGE", "NON_IMMATRICULEE"]


class Command(BaseCommand):
    help = "Peuple la base avec des données fictives (communes, propriétaires, parcelles, taxes)."

    def add_arguments(self, parser):
        parser.add_argument("--parcelles", type=int, default=120)

    def handle(self, *args, **options):
        nb_parcelles = options["parcelles"]

        self.stdout.write("Suppression des anciennes données...")
        Paiement.objects.all().delete()
        TaxeFonciere.objects.all().delete()
        Parcelle.objects.all().delete()
        Proprietaire.objects.all().delete()
        Commune.objects.all().delete()
        Actualite.objects.all().delete()

        # --- Communes ---
        communes = [
            Commune.objects.create(nom=nom, population_estimee=pop)
            for nom, pop in COMMUNES_THIES
        ]
        self.stdout.write(f"{len(communes)} communes créées.")

        # --- Propriétaires ---
        proprietaires = []
        for _ in range(60):
            est_morale = random.random() < 0.2
            proprietaires.append(Proprietaire.objects.create(
                type_proprietaire="MORALE" if est_morale else "PHYSIQUE",
                nom_complet=fake.company() if est_morale else fake.name(),
                telephone=fake.phone_number(),
                email=fake.email(),
                adresse=fake.address().replace("\n", ", "),
                nin_ou_rccm=fake.bothify("SN-########"),
            ))
        self.stdout.write(f"{len(proprietaires)} propriétaires créés.")

        # --- Parcelles + Taxes + Paiements ---
        parcelles = []
        for i in range(1, nb_parcelles + 1):
            commune = random.choice(communes)
            usage = random.choice(USAGES)
            superficie = Decimal(random.randint(80, 5000))
            valeur_m2 = {
                "RESIDENTIEL": 25000, "COMMERCIAL": 55000, "AGRICOLE": 4000,
                "INDUSTRIEL": 35000, "MIXTE": 30000,
            }[usage]
            valeur_venale = (superficie * valeur_m2 * Decimal(random.uniform(0.85, 1.25))).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )

            parcelle = Parcelle.objects.create(
                reference=f"TH-{2020 + (i % 6)}-{i:05d}",
                commune=commune,
                proprietaire=random.choice(proprietaires),
                quartier=fake.street_name(),
                superficie_m2=superficie,
                valeur_venale_fcfa=valeur_venale,
                usage=usage,
                statut=random.choice(STATUTS),
                latitude=Decimal(str(round(random.uniform(14.55, 14.95), 6))),
                longitude=Decimal(str(round(random.uniform(-17.15, -16.60), 6))),
            )
            parcelles.append(parcelle)

            # Taxes pour 1 à 3 années récentes
            for annee in random.sample([2023, 2024, 2025, 2026], k=random.randint(1, 3)):
                taux = TAUX_PAR_USAGE[usage]
                montant_du = (valeur_venale * taux).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                taxe = TaxeFonciere.objects.create(
                    parcelle=parcelle,
                    annee=annee,
                    taux_applique=taux,
                    montant_du=montant_du,
                    date_limite=date(annee, 12, 31),
                    statut="EMISE",
                )

                # Paiements aléatoires : payé totalement, partiellement, ou pas du tout
                r = random.random()
                if r < 0.55:
                    Paiement.objects.create(
                        taxe=taxe, montant=montant_du,
                        mode_paiement=random.choice(["ESPECES", "MOBILE_MONEY", "VIREMENT", "CHEQUE"]),
                        reference_transaction=fake.bothify("PMT-######"),
                    )
                    taxe.statut = "PAYEE"
                elif r < 0.8:
                    partiel = (montant_du * Decimal(random.uniform(0.2, 0.7))).quantize(Decimal("1"))
                    Paiement.objects.create(
                        taxe=taxe, montant=partiel,
                        mode_paiement=random.choice(["ESPECES", "MOBILE_MONEY", "VIREMENT"]),
                        reference_transaction=fake.bothify("PMT-######"),
                    )
                    taxe.statut = "PARTIELLEMENT_PAYEE"
                elif annee < 2026:
                    taxe.statut = "EN_RETARD"
                taxe.save()

        self.stdout.write(f"{len(parcelles)} parcelles créées avec taxes et paiements.")

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

        # --- Utilisateur agent de démonstration ---
        if not User.objects.filter(username="agent").exists():
            User.objects.create_superuser("agent", "agent@example.sn", "CadastreThies2026!")
            self.stdout.write(self.style.SUCCESS(
                "Utilisateur créé -> identifiant : agent / mot de passe : CadastreThies2026!"
            ))

        self.stdout.write(self.style.SUCCESS("Peuplement terminé avec succès."))

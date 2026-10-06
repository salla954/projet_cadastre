from django.urls import path
from . import views

app_name = "fiscalite"

urlpatterns = [
    path("taxes/", views.liste_taxes, name="liste_taxes"),
    path("taxes/<int:pk>/", views.detail_taxe, name="detail_taxe"),
    path("taxes/emettre/", views.emettre_taxe_recherche, name="emettre_taxe_recherche"),
    path("taxes/parcelle/<int:parcelle_pk>/emettre/", views.emettre_taxe, name="emettre_taxe"),
    path("taxes/payer/", views.enregistrer_paiement_recherche, name="enregistrer_paiement_recherche"),
    path("taxes/<int:taxe_pk>/payer/", views.enregistrer_paiement, name="enregistrer_paiement"),
    path("paiements/<int:paiement_pk>/quittance.pdf", views.quittance_paiement_pdf, name="quittance_paiement_pdf"),
]

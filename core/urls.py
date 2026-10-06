from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("comprendre-le-cadastre/", views.guide_cadastre, name="guide_cadastre"),
    path("actualites/", views.liste_actualites, name="liste_actualites"),
    path("actualites/<int:pk>/", views.detail_actualite, name="detail_actualite"),
    path("consultation/", views.consultation_publique, name="consultation_publique"),
    path("consultation/extrait-plan/<str:reference>/", views.extrait_plan_pdf, name="extrait_plan"),
    path("carte/", views.carte_parcelles, name="carte_parcelles"),
    path("carte/donnees.json/", views.carte_parcelles_donnees, name="carte_parcelles_donnees"),
    path("simulateur-taxe/", views.simulateur_taxe, name="simulateur_taxe"),
    path("services-utiles/", views.annuaire_services, name="annuaire_services"),
    path("modeles-documents/", views.modeles_documents, name="modeles_documents"),
    path("journal-activite/", views.journal_activite, name="journal_activite"),

    # Gestion des actualités (agents/administrateurs)
    path("gestion/actualites/", views.gestion_actualites, name="gestion_actualites"),
    path("gestion/actualites/nouvelle/", views.creer_actualite, name="creer_actualite"),
    path("gestion/actualites/<int:pk>/modifier/", views.modifier_actualite, name="modifier_actualite"),
    path("gestion/actualites/<int:pk>/supprimer/", views.supprimer_actualite, name="supprimer_actualite"),

    # Gestion des sections du guide du visiteur (agents/administrateurs)
    path("gestion/guide/", views.gestion_guide, name="gestion_guide"),
    path("gestion/guide/nouvelle/", views.creer_section_guide, name="creer_section_guide"),
    path("gestion/guide/<int:pk>/modifier/", views.modifier_section_guide, name="modifier_section_guide"),
    path("gestion/guide/<int:pk>/supprimer/", views.supprimer_section_guide, name="supprimer_section_guide"),
    path("gestion/guide/<int:pk>/deplacer/<str:direction>/", views.deplacer_section_guide, name="deplacer_section_guide"),
    path("gestion/guide/<int:pk>/basculer/", views.basculer_publication_section_guide, name="basculer_publication_section_guide"),
]

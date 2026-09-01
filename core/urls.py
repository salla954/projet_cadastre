from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("a-propos/", views.a_propos, name="a_propos"),
    path("comprendre-le-cadastre/", views.guide_cadastre, name="guide_cadastre"),
    path("actualites/", views.liste_actualites, name="liste_actualites"),
    path("actualites/<int:pk>/", views.detail_actualite, name="detail_actualite"),
    path("consultation/", views.consultation_publique, name="consultation_publique"),
    path("consultation/extrait-plan/<str:reference>/", views.extrait_plan_pdf, name="extrait_plan"),
    path("carte/", views.carte_parcelles, name="carte_parcelles"),
    path("carte/donnees.json/", views.carte_parcelles_donnees, name="carte_parcelles_donnees"),
]

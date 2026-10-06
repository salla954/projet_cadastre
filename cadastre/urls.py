from django.urls import path
from . import views

app_name = "cadastre"

urlpatterns = [
    path("parcelles/", views.liste_parcelles, name="liste_parcelles"),
    path("parcelles/<int:pk>/", views.detail_parcelle, name="parcelle_detail"),
    path("carte/rechercher-nicad/", views.rechercher_parcelle_nicad, name="rechercher_parcelle_nicad"),
    path("carte/parcelles/<int:pk>/mettre-a-jour/", views.mettre_a_jour_parcelle_carte, name="mettre_a_jour_parcelle_carte"),
]

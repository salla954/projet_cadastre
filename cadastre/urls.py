from django.urls import path
from . import views

app_name = "cadastre"

urlpatterns = [
    path("parcelles/", views.liste_parcelles, name="liste_parcelles"),
    path("parcelles/<int:pk>/", views.detail_parcelle, name="parcelle_detail"),
]

from django.urls import path
from . import views

app_name = "fiscalite"

urlpatterns = [
    path("taxes/", views.liste_taxes, name="liste_taxes"),
    path("taxes/<int:pk>/", views.detail_taxe, name="detail_taxe"),
]

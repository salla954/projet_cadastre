from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("agents/", views.statistiques_agents, name="statistiques_agents"),
]

from django.urls import path
from . import views

app_name = "appcadastre"

urlpatterns = [
    path("connexion/", views.ConnexionView.as_view(), name="connexion"),
    path("deconnexion/", views.DeconnexionView.as_view(), name="deconnexion"),
    path("utilisateurs/", views.liste_utilisateurs, name="liste_utilisateurs"),
    path("utilisateurs/nouveau/", views.creer_utilisateur, name="creer_utilisateur"),
    path("utilisateurs/<int:pk>/modifier/", views.modifier_utilisateur, name="modifier_utilisateur"),
]

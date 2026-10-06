from django.urls import path

from . import views

app_name = "demarches"

urlpatterns = [
    path("deposer/", views.choisir_type_dossier, name="deposer"),
    path("assistant/", views.assistant_demarche, name="assistant"),
    path("deposer/<str:type_dossier>/", views.deposer_dossier, name="deposer_type"),
    path("confirmation/<str:reference>/", views.confirmation_depot, name="confirmation"),
    path("confirmation/<str:reference>/recu.pdf", views.recu_dossier_pdf, name="recu_dossier_pdf"),
    path("suivre/", views.suivre_dossier, name="suivre"),
    path("mon-espace/", views.mon_espace, name="mon_espace"),
    path("mes-notifications/", views.mes_notifications, name="mes_notifications"),
    path("rendez-vous/", views.prendre_rdv, name="prendre_rdv"),
    path("rendez-vous/confirmation/<str:reference>/", views.confirmation_rdv, name="confirmation_rdv"),
    path("rendez-vous/confirmation/<str:reference>/recu.pdf", views.recu_rdv_pdf, name="recu_rdv_pdf"),
    path("agent/", views.liste_dossiers, name="liste_dossiers"),
    path("agent/<int:pk>/", views.detail_dossier, name="detail_dossier"),
    path("agent/rendez-vous/", views.liste_rdv, name="liste_rdv"),
    path("agent/rendez-vous/<int:pk>/", views.detail_rdv, name="detail_rdv"),
]

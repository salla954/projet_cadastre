from django.contrib import admin

from .models import Dossier, PieceJointe


class PieceJointeInline(admin.TabularInline):
    model = PieceJointe
    extra = 0
    readonly_fields = ("date_ajout",)


@admin.register(Dossier)
class DossierAdmin(admin.ModelAdmin):
    list_display = ("reference_suivi", "type_dossier", "nom_demandeur", "statut", "date_depot")
    list_filter = ("type_dossier", "statut")
    search_fields = ("reference_suivi", "nom_demandeur", "telephone_demandeur")
    readonly_fields = ("reference_suivi", "date_depot", "date_maj")
    inlines = [PieceJointeInline]

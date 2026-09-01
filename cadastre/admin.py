from django.contrib import admin
from .models import Commune, Proprietaire, Parcelle, PointBornage


@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    list_display = ("nom", "population_estimee")
    search_fields = ("nom",)


@admin.register(Proprietaire)
class ProprietaireAdmin(admin.ModelAdmin):
    list_display = ("nom_complet", "type_proprietaire", "telephone", "email")
    list_filter = ("type_proprietaire",)
    search_fields = ("nom_complet", "telephone", "nin_ou_rccm")


class PointBornageInline(admin.TabularInline):
    model = PointBornage
    extra = 4
    ordering = ("ordre",)
    fields = ("ordre", "label", "x", "y")


@admin.register(Parcelle)
class ParcelleAdmin(admin.ModelAdmin):
    list_display = (
        "reference", "commune", "proprietaire", "usage",
        "statut", "superficie_m2", "valeur_venale_fcfa",
    )
    list_filter = ("commune", "usage", "statut")
    search_fields = ("reference", "quartier", "proprietaire__nom_complet")
    autocomplete_fields = ("proprietaire", "commune")
    inlines = [PointBornageInline]

from django.contrib import admin
from .models import TaxeFonciere, Paiement


class PaiementInline(admin.TabularInline):
    model = Paiement
    extra = 0


@admin.register(TaxeFonciere)
class TaxeFonciereAdmin(admin.ModelAdmin):
    list_display = (
        "parcelle", "annee", "montant_du", "montant_paye",
        "solde_restant", "statut",
    )
    list_filter = ("annee", "statut")
    search_fields = ("parcelle__reference",)
    inlines = [PaiementInline]


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ("taxe", "montant", "mode_paiement", "date_paiement")
    list_filter = ("mode_paiement",)

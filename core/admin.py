from django.contrib import admin
from .models import Actualite


@admin.register(Actualite)
class ActualiteAdmin(admin.ModelAdmin):
    list_display = ("titre", "date_publication", "publie")
    list_filter = ("publie",)
    search_fields = ("titre", "contenu")

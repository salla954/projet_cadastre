from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Profil


class ProfilInline(admin.StackedInline):
    model = Profil
    can_delete = False
    verbose_name_plural = "Profil (rôle)"


class UserAdmin(DjangoUserAdmin):
    inlines = (ProfilInline,)
    list_display = ("username", "email", "role_affiche", "is_staff", "is_superuser", "is_active")

    @admin.display(description="Rôle")
    def role_affiche(self, obj):
        return getattr(obj, "profil", None) and obj.profil.get_role_display()

    def save_formset(self, request, form, formset, change):
        if formset.model is Profil and not change:
            # À la création d'un utilisateur, le signal post_save (voir
            # appcadastre/signals.py) a déjà créé un Profil pour lui. Ce
            # formulaire intégré ne le sait pas et tenterait d'en insérer un
            # second pour le même utilisateur (violation de la contrainte
            # d'unicité) — on reporte donc les champs saisis sur l'instance
            # déjà existante plutôt que d'enregistrer l'instance transitoire
            # du formulaire (qui n'a pas de date_creation valide).
            instances = formset.save(commit=False)
            for instance in instances:
                profil_existant = Profil.objects.filter(utilisateur=instance.utilisateur).first()
                if profil_existant:
                    profil_existant.role = instance.role
                    profil_existant.telephone = instance.telephone
                    profil_existant.service = instance.service
                    profil_existant.save()
                else:
                    instance.save()
            formset.save_m2m()
        else:
            formset.save()


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "role", "service", "telephone", "date_creation")
    list_filter = ("role",)
    search_fields = ("utilisateur__username", "utilisateur__email", "service")

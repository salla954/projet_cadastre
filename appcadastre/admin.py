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


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "role", "service", "telephone", "date_creation")
    list_filter = ("role",)
    search_fields = ("utilisateur__username", "utilisateur__email", "service")

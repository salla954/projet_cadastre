# Data migration : crée un Profil pour les utilisateurs déjà présents en base
# (comptes créés avant l'introduction du système de rôles).

from django.db import migrations


def creer_profils_manquants(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Profil = apps.get_model('appcadastre', 'Profil')

    for utilisateur in User.objects.all():
        if not Profil.objects.filter(utilisateur_id=utilisateur.pk).exists():
            role = 'ADMINISTRATEUR' if utilisateur.is_superuser else 'AGENT'
            Profil.objects.create(utilisateur_id=utilisateur.pk, role=role)


def supprimer_profils(apps, schema_editor):
    Profil = apps.get_model('appcadastre', 'Profil')
    Profil.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('appcadastre', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(creer_profils_manquants, supprimer_profils),
    ]

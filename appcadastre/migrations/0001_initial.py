# Generated manually to match project conventions (Django 6.0.7)

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profil',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('ADMINISTRATEUR', 'Administrateur'), ('AGENT', 'Agent'), ('VISITEUR', 'Visiteur')], default='AGENT', max_length=20)),
                ('telephone', models.CharField(blank=True, max_length=20)),
                ('service', models.CharField(blank=True, help_text='Ex : Service du Cadastre, Service des Impôts...', max_length=100)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('utilisateur', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profil', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Profil utilisateur',
                'verbose_name_plural': 'Profils utilisateurs',
            },
        ),
    ]

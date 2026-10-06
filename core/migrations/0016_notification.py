# Generated manually to match project conventions (Django 6.0.7)

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_journalactivite'),
        ('demarches', '0004_rendezvous'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telephone_destinataire', models.CharField(help_text='Copié depuis le dossier/rendez-vous au moment de la création.', max_length=20, verbose_name='Téléphone du destinataire')),
                ('message', models.CharField(max_length=255, verbose_name='Message')),
                ('date_creation', models.DateTimeField(auto_now_add=True, verbose_name='Date')),
                ('dossier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='demarches.dossier', verbose_name='Dossier concerné')),
                ('rendez_vous', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='demarches.rendezvous', verbose_name='Rendez-vous concerné')),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'ordering': ['-date_creation'],
            },
        ),
    ]

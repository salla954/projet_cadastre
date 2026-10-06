# Generated manually to match project conventions (Django 6.0.7)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appcadastre', '0002_profils_utilisateurs_existants'),
        ('cadastre', '0004_extraitplangenere'),
    ]

    operations = [
        migrations.AddField(
            model_name='profil',
            name='specialite',
            field=models.CharField(
                blank=True,
                choices=[
                    ('GENERALISTE', 'Généraliste'),
                    ('CADASTRE', 'Cadastre'),
                    ('FISCALITE', 'Fiscalité'),
                    ('ACCUEIL', 'Accueil & rendez-vous'),
                ],
                default='GENERALISTE',
                help_text="Domaine principal de responsabilité de cet agent (facultatif, pour orienter l'attribution des dossiers).",
                max_length=20,
                verbose_name='Spécialité / mission',
            ),
        ),
        migrations.AddField(
            model_name='profil',
            name='communes_attribuees',
            field=models.ManyToManyField(
                blank=True,
                help_text='Communes dont cet agent a la charge. Laisser vide pour toutes les communes.',
                related_name='agents_attribues',
                to='cadastre.commune',
                verbose_name='Communes attribuées',
            ),
        ),
    ]

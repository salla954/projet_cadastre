from django.db import models


class Actualite(models.Model):
    """Article d'information publié sur le site public (actualités, guides, avis)."""
    titre = models.CharField(max_length=200)
    chapo = models.CharField("Chapô (résumé court)", max_length=300)
    contenu = models.TextField()
    date_publication = models.DateTimeField(auto_now_add=True)
    publie = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Actualité"
        verbose_name_plural = "Actualités"
        ordering = ["-date_publication"]

    def __str__(self):
        return self.titre

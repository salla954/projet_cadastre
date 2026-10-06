from django import forms

from .models import Actualite, SectionGuide


class ActualiteForm(forms.ModelForm):
    class Meta:
        model = Actualite
        fields = ["titre", "chapo", "contenu", "date_publication", "source_url", "publie"]
        widgets = {
            "chapo": forms.Textarea(attrs={"rows": 2}),
            "contenu": forms.Textarea(attrs={"rows": 6}),
            "date_publication": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date_publication"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["source_url"].required = False


class SectionGuideForm(forms.ModelForm):
    class Meta:
        model = SectionGuide
        fields = ["titre", "categorie", "contenu", "ordre", "publie"]
        widgets = {
            "contenu": forms.Textarea(attrs={"rows": 10}),
        }

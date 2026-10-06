import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

# Syntaxe volontairement minimale et sûre : [texte du lien](url)
_MOTIF_LIEN = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+|/[^\s)]+)\)")

# Paragraphes reconnus comme des remarques à mettre en valeur (carte "astuce")
# plutôt qu'affichés comme un paragraphe de texte ordinaire.
_PREFIXES_ASTUCE = ("Bon à savoir", "Astuce", "À noter", "Important", "Attention")


def _rendre_item_liste(ligne):
    """Rend un élément de liste ("- Étiquette : détail" ou "- Simple item") en
    mettant en gras l'étiquette quand le motif "Étiquette : détail" est présent."""
    texte = ligne.lstrip()[2:]
    etiquette, separateur, reste = texte.partition(" : ")
    if separateur:
        return f"<strong>{etiquette}</strong> : {reste}"
    return texte


def _rendre_checklist(lignes):
    """Rend une série de lignes "- " sous forme de grille de cases numérotées."""
    cases = "".join(
        f'<div class="check-item"><span class="puce">{i}</span><span>{_rendre_item_liste(ligne)}</span></div>'
        for i, ligne in enumerate(lignes, start=1)
    )
    return f'<div class="checklist">{cases}</div>'


def _rendre_paragraphe(bloc, est_premier=False):
    """Rend un bloc de texte (déjà échappé) en HTML, façon "fiches numérotées" :
    - un bloc dont toutes les lignes commencent par "- " devient une grille de
      cases numérotées (plutôt qu'une liste à puces classique) ;
    - une ligne d'introduction suivie uniquement de lignes "- " (dans le même
      bloc, sans ligne vide entre les deux) garde son introduction en texte et
      transforme le reste en grille de cases numérotées ;
    - un bloc qui commence par un mot-clé comme "Astuce :" ou "À noter :"
      devient une carte mise en avant plutôt qu'un paragraphe ordinaire ;
    - le tout premier paragraphe de texte de la section devient un encadré
      "définition", pour donner un point d'entrée visuel immédiat.
    """
    lignes = [ligne for ligne in bloc.split("\n") if ligne.strip()]

    if lignes and all(ligne.lstrip().startswith("- ") for ligne in lignes):
        return _rendre_checklist(lignes)

    if len(lignes) > 1 and all(ligne.lstrip().startswith("- ") for ligne in lignes[1:]):
        return f"<p>{lignes[0]}</p>{_rendre_checklist(lignes[1:])}"

    for prefixe in _PREFIXES_ASTUCE:
        if bloc.startswith(prefixe + " :"):
            etiquette, separateur, reste = bloc.partition(" :")
            reste_html = reste.strip().replace(chr(10), "<br>")
            return (
                f'<div class="carte-astuce"><span class="icone">💡</span>'
                f"<div><strong>{etiquette}</strong>{reste_html}</div></div>"
            )

    texte_html = bloc.replace(chr(10), "<br>")
    classe = ' class="definition"' if est_premier else ""
    return f"<p{classe}>{texte_html}</p>"


@register.filter
def texte_riche(valeur, mode=None):
    """Affiche un texte saisi par un agent en échappant tout HTML potentiellement
    dangereux, tout en convertissant la syntaxe simple [texte](url) en vrais liens
    cliquables, les blocs de lignes "- " en grilles de cases numérotées, les
    remarques ("Astuce :", "À noter :"...) en cartes mises en avant, et le tout
    premier paragraphe en encadré "définition" — le tout dans l'esprit "fiches
    numérotées" retenu pour le guide du visiteur.

    Passer "simple" comme argument désactive uniquement l'encadré "définition"
    sur le premier paragraphe (utile pour un texte déjà imbriqué dans un autre
    encadré, comme une réponse de FAQ, où l'effet ferait doublon).

    Utilisé pour le contenu du guide du visiteur, saisi en texte libre par les
    agents (pas de formulaire riche/HTML autorisé, pour éviter tout risque
    d'injection tout en gardant la possibilité d'inclure des liens utiles).
    """
    if not valeur:
        return ""
    texte_echappe = escape(valeur)
    texte_avec_liens = _MOTIF_LIEN.sub(r'<a href="\2">\1</a>', texte_echappe)
    paragraphes = [p for p in texte_avec_liens.split("\n\n") if p.strip()]
    html = "".join(
        _rendre_paragraphe(bloc, est_premier=(mode != "simple" and i == 0))
        for i, bloc in enumerate(paragraphes)
    )
    return mark_safe(html)

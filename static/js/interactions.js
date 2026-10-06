// Petites interactions progressives : révélation au défilement + compteurs animés.
// Tout est conçu pour se dégrader proprement si JS est désactivé (les valeurs
// réelles sont déjà présentes dans le HTML côté serveur) et pour respecter
// prefers-reduced-motion.
document.addEventListener('DOMContentLoaded', function () {
  var reduitMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------- Révélation au défilement ----------
  var elementsReveal = document.querySelectorAll('.reveal');
  if (elementsReveal.length) {
    if (reduitMotion || typeof IntersectionObserver === 'undefined') {
      elementsReveal.forEach(function (el) { el.classList.add('visible'); });
    } else {
      var observateur = new IntersectionObserver(function (entrees) {
        entrees.forEach(function (entree) {
          if (entree.isIntersecting) {
            entree.target.classList.add('visible');
            observateur.unobserve(entree.target);
          }
        });
      }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
      elementsReveal.forEach(function (el) { observateur.observe(el); });
    }
  }

  // ---------- Compteurs animés (chiffres clés) ----------
  var compteurs = document.querySelectorAll('.chiffre-nombre');
  if (compteurs.length && !reduitMotion) {
    var animerCompteur = function (el) {
      var cible = parseFloat(el.getAttribute('data-valeur')) || 0;
      var texteFinal = el.innerHTML; // valeur déjà formatée par Django (séparateurs de milliers)
      var duree = 1400;
      var depart = null;

      el.textContent = '0';

      function etape(horodatage) {
        if (!depart) depart = horodatage;
        var progression = Math.min((horodatage - depart) / duree, 1);
        var facilite = 1 - Math.pow(1 - progression, 3); // ease-out cubique
        el.textContent = Math.round(facilite * cible).toLocaleString('en-US');
        if (progression < 1) {
          window.requestAnimationFrame(etape);
        } else {
          el.innerHTML = texteFinal; // valeur exacte garantie à la fin
        }
      }
      window.requestAnimationFrame(etape);
    };

    if (typeof IntersectionObserver === 'undefined') {
      compteurs.forEach(animerCompteur);
    } else {
      var observateurCompteurs = new IntersectionObserver(function (entrees) {
        entrees.forEach(function (entree) {
          if (entree.isIntersecting) {
            animerCompteur(entree.target);
            observateurCompteurs.unobserve(entree.target);
          }
        });
      }, { threshold: 0.4 });
      compteurs.forEach(function (el) { observateurCompteurs.observe(el); });
    }
  }

  // ---------- Barre de progression de lecture ----------
  var barre = document.querySelector('.barre-progression span');
  if (barre) {
    var majBarre = function () {
      var h = document.documentElement;
      var hauteurScrollable = h.scrollHeight - h.clientHeight;
      var pourcentage = hauteurScrollable > 0 ? (h.scrollTop / hauteurScrollable) * 100 : 0;
      barre.style.width = pourcentage + '%';
    };
    window.addEventListener('scroll', majBarre, { passive: true });
    window.addEventListener('resize', majBarre);
    majBarre();
  }

  // ---------- Effet tilt léger au survol des cartes ----------
  if (!reduitMotion && window.matchMedia && window.matchMedia('(hover: hover)').matches) {
    var cartesTilt = document.querySelectorAll('.service-carte, .actu-carte');
    cartesTilt.forEach(function (carte) {
      carte.addEventListener('mousemove', function (e) {
        var rect = carte.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var y = e.clientY - rect.top;
        var rotX = ((y - rect.height / 2) / (rect.height / 2)) * -5;
        var rotY = ((x - rect.width / 2) / (rect.width / 2)) * 5;
        carte.style.transform =
          'perspective(900px) rotateX(' + rotX + 'deg) rotateY(' + rotY + 'deg) translateY(-4px)';
      });
      carte.addEventListener('mouseleave', function () {
        carte.style.transform = '';
      });
    });
  }

  // ---------- Effet "ripple" au clic sur les boutons ----------
  if (!reduitMotion) {
    var boutons = document.querySelectorAll('.btn');
    boutons.forEach(function (bouton) {
      // Calque vide superposé, uniquement pour contenir/rogner les vagues :
      // le texte du bouton reste en flux normal, sa taille n'est donc jamais affectée.
      var enveloppe = document.createElement('span');
      enveloppe.className = 'ripple-enveloppe';
      bouton.appendChild(enveloppe);

      bouton.addEventListener('click', function (e) {
        var rect = bouton.getBoundingClientRect();
        var taille = Math.max(rect.width, rect.height) * 2;
        var vague = document.createElement('span');
        vague.className = 'ripple';
        vague.style.width = vague.style.height = taille + 'px';
        vague.style.left = (e.clientX - rect.left - taille / 2) + 'px';
        vague.style.top = (e.clientY - rect.top - taille / 2) + 'px';
        enveloppe.appendChild(vague);
        vague.addEventListener('animationend', function () { vague.remove(); });
      });
    });
  }

  // ---------- Modale de connexion agent ----------
  var modalConnexion = document.getElementById('modal-connexion');
  if (modalConnexion) {
    var fermerAvecEchap = function (e) {
      if (e.key === 'Escape') fermerModalConnexion();
    };
    var ouvrirModalConnexion = function () {
      modalConnexion.classList.add('ouvert');
      modalConnexion.setAttribute('aria-hidden', 'false');
      var champUsername = document.getElementById('modal-id-username');
      if (champUsername) champUsername.focus();
      document.addEventListener('keydown', fermerAvecEchap);
    };
    var fermerModalConnexion = function () {
      modalConnexion.classList.remove('ouvert');
      modalConnexion.setAttribute('aria-hidden', 'true');
      document.removeEventListener('keydown', fermerAvecEchap);
    };

    document.querySelectorAll('[data-ouvre-connexion]').forEach(function (lien) {
      lien.addEventListener('click', function (e) {
        e.preventDefault();
        ouvrirModalConnexion();
      });
    });
    modalConnexion.querySelectorAll('[data-fermer-modal]').forEach(function (el) {
      el.addEventListener('click', fermerModalConnexion);
    });

    var formulaireConnexion = document.getElementById('formulaire-connexion-modal');
    var messageErreurConnexion = document.getElementById('modal-connexion-erreur');
    if (formulaireConnexion) {
      formulaireConnexion.addEventListener('submit', function (e) {
        e.preventDefault();
        messageErreurConnexion.style.display = 'none';
        var donnees = new FormData(formulaireConnexion);

        fetch(formulaireConnexion.action, {
          method: 'POST',
          body: donnees,
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
          .then(function (reponse) {
            return reponse.json().then(function (corps) {
              return { ok: reponse.ok, corps: corps };
            });
          })
          .then(function (resultat) {
            if (resultat.ok && resultat.corps.succes) {
              window.location.href = resultat.corps.redirection || '/';
            } else {
              messageErreurConnexion.textContent =
                (resultat.corps && resultat.corps.erreur) || 'Identifiant ou mot de passe incorrect.';
              messageErreurConnexion.style.display = 'block';
            }
          })
          .catch(function () {
            messageErreurConnexion.textContent = 'Une erreur est survenue. Réessayez.';
            messageErreurConnexion.style.display = 'block';
          });
      });
    }
  }

  // ---------- Sous-menus de navigation (Démarches, Ressources, Contenu) ----------
  var groupesNav = document.querySelectorAll('.nav-groupe');
  if (groupesNav.length) {
    groupesNav.forEach(function (groupe) {
      groupe.addEventListener('toggle', function () {
        if (groupe.open) {
          groupesNav.forEach(function (autre) {
            if (autre !== groupe) autre.open = false;
          });
        }
      });
    });
    document.addEventListener('click', function (e) {
      groupesNav.forEach(function (groupe) {
        if (groupe.open && !groupe.contains(e.target)) groupe.open = false;
      });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        groupesNav.forEach(function (groupe) { groupe.open = false; });
      }
    });
  }
});

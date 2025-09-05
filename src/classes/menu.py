import os

import pygame
from .bouton import Bouton

# ------------------- COULEURS PAR DÉFAUT -------------------
BLANC = (255, 255, 255)
GRIS = (200, 200, 200)
NOIR = (0, 0, 0)

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


COULEURS_BOUTON = {
    "fond_normal": BLANC,
    "fond_survol": GRIS,
    "contour": NOIR,
    "texte": NOIR,
}

CREDITS_LIGNES = [
    "Protect The Castle",
    "",
    "Equipe :",
    "BENKHEIRA Lilya",
    "BOUGHENDJOUR Rahim",
    "D'ETTORRE Yvan",
    "GIBELLO Gregoire",
    "GIMBERT Bastien",
    "",
    "Assets : free-game-assets.itch.io (achetés sous licence)",
    "",
    "Musiques (arrangements bardcore) :",
    "Barbie Girl (Aqua)",
    "Havana (Camila Cabello)",
    "Crab Rave (Noisestorm)",
    "Smells Like Teen Spirit (Nirvana)",
    "Hips Don't Lie (Shakira)",
    "We Found Love (Rihanna)",
    "",
    "Arrangements médiévaux : Stantough",
    "",
    "Merci d'avoir joué !",
    "2025"
]

# ------------------- IMAGE DE FOND --------------------
FOND = None
def charger_fond(ecran: pygame.Surface):
    global FOND
    if FOND is None:  # on le fait une seule fois
        image = pygame.image.load(os.path.join(base_dir, "assets", "fond.png")).convert()
        FOND = pygame.transform.scale(image, ecran.get_size())

# ------------------- CRÉDITS -------------------
SCROLL_VITESSE = 1.0
ESPACEMENT_LIGNES = 54
MARGE_DEPART = 80
_scroll_y = None

# ------------------- FABRICATION DES BOUTONS -------------------

def creer_boutons_menu(police: pygame.font.Font, reprendre: bool, actions: dict) -> list:
    """
    Construit la liste des boutons du menu principal ou du menu pause.
    - reprendre=False => affiche un bouton "Jouer", sinon "Reprendre".
    - actions: dictionnaire contenant les callbacks {"jouer": fn, "reprendre": fn, "credits": fn, "muet": fn, "quitter": fn}
    """
    boutons = []

    largeur_ecran = 1168
    hauteur_bouton = 50
    largeur_bouton = 200
    espacement = 50
    y_depart = 300

    if reprendre:
        boutons.append(Bouton("Reprendre", (largeur_ecran - largeur_bouton) // 2, y_depart, largeur_bouton, hauteur_bouton, actions.get("reprendre"), police, COULEURS_BOUTON))
    else:
        boutons.append(Bouton("Jouer", (largeur_ecran - largeur_bouton) // 2, y_depart, largeur_bouton, hauteur_bouton, actions.get("jouer"), police, COULEURS_BOUTON))

    boutons.append(Bouton("Crédits", (largeur_ecran - largeur_bouton) // 2, y_depart + (hauteur_bouton + espacement), largeur_bouton, hauteur_bouton, actions.get("credits"), police, COULEURS_BOUTON))
    boutons.append(Bouton("Muet", (largeur_ecran - largeur_bouton) // 2, y_depart + 2 * (hauteur_bouton + espacement), largeur_bouton, hauteur_bouton, actions.get("muet"), police, COULEURS_BOUTON))
    boutons.append(Bouton("Quitter", (largeur_ecran - largeur_bouton) // 2, y_depart + 3 * (hauteur_bouton + espacement), largeur_bouton, hauteur_bouton, actions.get("quitter"), police, COULEURS_BOUTON))

    return boutons


def creer_boutons_credits(police: pygame.font.Font, action_retour) -> list:
    """Construit le bouton de retour depuis l'écran des crédits."""
    return [
        Bouton("Retour", 968, 720, 200, 50, action_retour, police, COULEURS_BOUTON)
    ]

# ------------------- AFFICHAGES -------------------

def dessiner_menu(ecran: pygame.Surface, boutons: list) -> None:
    """Dessine le fond et les boutons du menu (principal ou pause)."""
    charger_fond(ecran)
    ecran.blit(FOND, (0, 0))
    for b in boutons:
        b.dessiner(ecran)

def dessiner_credits(ecran: pygame.Surface, police: pygame.font.Font, largeur: int) -> None:
    """
    Affiche un défilement vertical des crédits (de bas en haut).
    """
    global _scroll_y

    w, h = ecran.get_size()
    ecran.fill((0, 0, 0))

    if _scroll_y is None:
        _scroll_y = h + MARGE_DEPART

    for i, ligne in enumerate(CREDITS_LIGNES):
        surf = police.render(ligne, True, BLANC)
        y = _scroll_y + i * ESPACEMENT_LIGNES
        if -ESPACEMENT_LIGNES < y < h + ESPACEMENT_LIGNES: 
            ecran.blit(surf, (w // 2 - surf.get_width() // 2, y))

    # avancer le défilement
    _scroll_y -= SCROLL_VITESSE


# ------------------- GAME OVER -------------------

_GAMEOVER_IMG = None

def _charger_gameover(ecran: pygame.Surface):
    global _GAMEOVER_IMG
    if _GAMEOVER_IMG is None:
        chemin = os.path.join(base_dir, "assets", "gameover.png")
        if os.path.exists(chemin):
            try:
                img = pygame.image.load(chemin).convert_alpha()
                _GAMEOVER_IMG = pygame.transform.smoothscale(img, ecran.get_size())
            except Exception:
                _GAMEOVER_IMG = None

def creer_boutons_gameover(police: pygame.font.Font, actions: dict) -> list:
    largeur_ecran = 1168
    largeur_bouton = 260
    hauteur_bouton = 56
    espacement = 24
    y_depart = 520

    boutons = [
        Bouton("Recommencer", (largeur_ecran - largeur_bouton) // 2, y_depart, largeur_bouton, hauteur_bouton, actions.get("recommencer"), police, COULEURS_BOUTON),
        Bouton("Crédits", (largeur_ecran - largeur_bouton) // 2, y_depart + (hauteur_bouton + espacement), largeur_bouton, hauteur_bouton, actions.get("credits"), police, COULEURS_BOUTON),
        Bouton("Quitter", (largeur_ecran - largeur_bouton) // 2, y_depart + 2 * (hauteur_bouton + espacement), largeur_bouton, hauteur_bouton, actions.get("quitter"), police, COULEURS_BOUTON),
    ]
    return boutons

def dessiner_gameover(ecran: pygame.Surface, boutons: list) -> None:
    _charger_gameover(ecran)
    if _GAMEOVER_IMG is not None:
        ecran.blit(_GAMEOVER_IMG, (0, 0))
    else:
        ecran.fill((20, 0, 0))
        # Titre fallback
        try:
            police_titre = pygame.font.Font(None, 96)
        except Exception:
            police_titre = None
        if police_titre is not None:
            titre = police_titre.render("GAME OVER", True, (220, 40, 40))
            ecran.blit(titre, (ecran.get_width() // 2 - titre.get_width() // 2, 180))

    for b in boutons:
        b.dessiner(ecran)

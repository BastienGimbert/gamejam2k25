import pygame
from bouton import Bouton

# ------------------- COULEURS PAR DÉFAUT -------------------
BLANC = (255, 255, 255)
GRIS = (200, 200, 200)
NOIR = (0, 0, 0)

COULEURS_BOUTON = {
    "fond_normal": BLANC,
    "fond_survol": GRIS,
    "contour": NOIR,
    "texte": NOIR,
}

# ------------------- FABRICATION DES BOUTONS -------------------

def creer_boutons_menu(police: pygame.font.Font, reprendre: bool, actions: dict) -> list:
    """
    Construit la liste des boutons du menu principal ou du menu pause.
    - reprendre=False => affiche un bouton "Jouer", sinon "Reprendre".
    - actions: dictionnaire contenant les callbacks {"jouer": fn, "reprendre": fn, "credits": fn, "muet": fn, "quitter": fn}
    """
    boutons = []

    if reprendre:
        boutons.append(Bouton("Reprendre", 300, 200, 200, 50, actions.get("reprendre"), police, COULEURS_BOUTON))
    else:
        boutons.append(Bouton("Jouer", 300, 200, 200, 50, actions.get("jouer"), police, COULEURS_BOUTON))

    boutons.append(Bouton("Crédits", 300, 300, 200, 50, actions.get("credits"), police, COULEURS_BOUTON))
    boutons.append(Bouton("Muet", 300, 400, 200, 50, actions.get("muet"), police, COULEURS_BOUTON))
    boutons.append(Bouton("Quitter", 300, 500, 200, 50, actions.get("quitter"), police, COULEURS_BOUTON))

    return boutons


def creer_boutons_credits(police: pygame.font.Font, action_retour) -> list:
    """Construit le bouton de retour depuis l'écran des crédits."""
    return [
        Bouton("Retour", 300, 500, 200, 50, action_retour, police, COULEURS_BOUTON)
    ]

# ------------------- AFFICHAGES -------------------

def dessiner_menu(ecran: pygame.Surface, boutons: list) -> None:
    """Dessine le fond et les boutons du menu (principal ou pause)."""
    ecran.fill((100, 150, 200))
    for b in boutons:
        b.dessiner(ecran)


def dessiner_credits(ecran: pygame.Surface, police: pygame.font.Font, largeur: int) -> None:
    """Dessine l'écran des crédits."""
    ecran.fill((180, 180, 180))
    lignes = ["Protect The Castle", "Par ...", "2025"]
    for i, ligne in enumerate(lignes):
        surf = police.render(ligne, True, NOIR)
        ecran.blit(surf, (largeur // 2 - surf.get_width() // 2, 150 + i * 60))

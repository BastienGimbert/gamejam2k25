import os
import random
import sys

import pygame

from classes.constants import AUDIO_DIR, FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from classes.menu import (
    creer_boutons_credits,
    creer_boutons_menu,
    dessiner_credits,
    dessiner_menu,
    afficher_regles,
)
from classes.bouton import Bouton
from game import Game

# ------------------- INITIALISATION -------------------
pygame.init()
# Initialisation du mixer pour gérer le volume (muet)
try:
    pygame.mixer.init()
    MIXER_DISPONIBLE = True
except Exception:
    # Si pas de périphérique audio dispo, on continue sans mixer
    MIXER_DISPONIBLE = False

ECRAN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Protect The Castle")

POLICE = pygame.font.Font(None, 50)
HORLOGE = pygame.time.Clock()

# Etats possibles: "MENU", "JEU", "PAUSE", "CREDITS", "GAMEOVER"
ETAT = "MENU"
ETAT_AVANT_CREDITS = "MENU"

# ------------------- MUSIQUE DE FOND -------------------

# Gestion du son (muet ou non)
est_muet = False
VOLUME_MUSIQUE = 1.0

# événement pour musique terminée
MUSIQUE_FINIE = pygame.USEREVENT + 1
pygame.mixer.music.set_endevent(MUSIQUE_FINIE)

derniere_piste = None  # piste jouée précédemment

page_regles = 0

def demarrer_musique_de_fond() -> None:
    """Choisit une musique aléatoirement et la joue"""
    global derniere_piste
    if not MIXER_DISPONIBLE:
        return
    pistes_candidates = [
        os.path.join(AUDIO_DIR, "Aqua-Barbie-Girl.mp3"),
        os.path.join(AUDIO_DIR, "Camila-Cabello-Havana.mp3"),
        os.path.join(AUDIO_DIR, "Crab-Rave-medieval-style.mp3"),
        os.path.join(AUDIO_DIR, "Nirvana-Smells-Like-Teen-Spirit.mp3"),
        os.path.join(AUDIO_DIR, "Shakira-Hips-Don-t-Lie.mp3"),
        os.path.join(AUDIO_DIR, "We-Found-Love-Bardcore.mp3"),
    ]

    # Filtrer celles qui existent vraiment
    pistes_existantes = [p for p in pistes_candidates if os.path.exists(p)]
    if not pistes_existantes:
        print("Aucune piste musicale trouvée.")
        return

    # Choisir une piste différente de la précédente
    choix = random.choice(pistes_existantes)
    while len(pistes_existantes) > 1 and choix == derniere_piste:
        choix = random.choice(pistes_existantes)

    derniere_piste = choix

    try:
        pygame.mixer.music.load(choix)
        pygame.mixer.music.set_volume(0.0 if est_muet else VOLUME_MUSIQUE)
        pygame.mixer.music.play()
        print(f"Musique choisie et lancée : {choix}")
    except Exception as e:
        print(f"Impossible de charger la musique {choix}: {e}")
    # Si aucune piste trouvée/chargée, on ignore silencieusement
    return


# Lancer la musique au démarrage
demarrer_musique_de_fond()

# ------------------- CALLBACKS D'ACTION -------------------


def demarrer_jeu():
    global ETAT
    ETAT = "JEU"
    # scene_jeu.lancerVague()

def afficher_regles_callback():
    global ETAT
    ETAT = "REGLES"

def reprendre_jeu():
    global ETAT
    ETAT = "JEU"


def afficher_credits():
    global ETAT, ETAT_AVANT_CREDITS
    # mémorise l'état actuel pour y revenir en quittant les crédits
    ETAT_AVANT_CREDITS = ETAT
    ETAT = "CREDITS"


def basculer_muet():
    global est_muet
    est_muet = not est_muet
    # Met le volume musique à 0 si muet, sinon remet le volume normal
    if MIXER_DISPONIBLE:
        pygame.mixer.music.set_volume(0.0 if est_muet else VOLUME_MUSIQUE)
    print("Muet activé" if est_muet else "Son activé")
    # Propager l'état muet au jeu pour les SFX
    try:
        scene_jeu.est_muet = est_muet
    except Exception:
        pass


def retour_depuis_credits():
    global ETAT
    ETAT = (
        ETAT_AVANT_CREDITS
        if ETAT_AVANT_CREDITS in {"MENU", "PAUSE", "JEU", "GAMEOVER"}
        else "MENU"
    )


def quitter_jeu():
    """Ferme proprement Pygame et le programme."""
    pygame.quit()
    sys.exit()


# ------------------- CONSTRUCTION DES ÉCRANS -------------------


# Game (scène)
scene_jeu = Game(POLICE, est_muet=est_muet)

ACTIONS_MENU_PRINCIPAL = {
    "jouer": demarrer_jeu,
    "regles": afficher_regles_callback,
    "credits": afficher_credits,
    "muet": basculer_muet,
    "quitter": quitter_jeu,
}

ACTIONS_MENU_PAUSE = {
    "reprendre": reprendre_jeu,
    "credits": afficher_credits,
    "muet": basculer_muet,
    "quitter": quitter_jeu,
}

BOUTONS_MENU = creer_boutons_menu(
    POLICE, reprendre=False, actions=ACTIONS_MENU_PRINCIPAL
)
BOUTONS_PAUSE = creer_boutons_menu(POLICE, reprendre=True, actions=ACTIONS_MENU_PAUSE)
BOUTONS_CREDITS = creer_boutons_credits(POLICE, action_retour=retour_depuis_credits)

def retour_depuis_regles():
    global ETAT
    ETAT = "MENU"
BOUTONS_REGLES = [Bouton("Retour", WINDOW_WIDTH - 220, WINDOW_HEIGHT - 80, 160, 50, retour_depuis_regles, POLICE, {
    "fond_normal": (255, 255, 255),
    "fond_survol": (200, 200, 200),
    "contour": (0, 0, 0),
    "texte": (0, 0, 0),
})]

# Game Over
ACTIONS_GAMEOVER = {
    "recommencer": lambda: redemarrer_partie(),
    "credits": afficher_credits,
    "quitter": lambda: quitter_jeu(),
}


def redemarrer_partie():
    global scene_jeu, ETAT
    scene_jeu = Game(POLICE, est_muet=est_muet)
    ETAT = "JEU"


try:
    from classes.menu import creer_boutons_gameover, dessiner_gameover

    BOUTONS_GAMEOVER = creer_boutons_gameover(POLICE, actions=ACTIONS_GAMEOVER)
except Exception:
    # Fallback si la fonction n'existe pas (ancienne version): pas de boutons spécifiques
    BOUTONS_GAMEOVER = []

    def dessiner_gameover(ecran: pygame.Surface, boutons: list):
        ecran.fill((0, 0, 0))
        txt = POLICE.render("Game Over", True, (255, 0, 0))
        ecran.blit(txt, (ECRAN.get_width() // 2 - txt.get_width() // 2, 200))
        for b in boutons:
            b.dessiner(ecran)


# ------------------- BOUCLE PRINCIPALE -------------------


def main() -> None:
    global ETAT

    while True:
        # 1) Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == MUSIQUE_FINIE:
                demarrer_musique_de_fond()

            if ETAT == "MENU":
                for b in BOUTONS_MENU:
                    b.gerer_evenement(event)
            elif ETAT == "PAUSE":
                for b in BOUTONS_PAUSE:
                    b.gerer_evenement(event)
            elif ETAT == "CREDITS":
                for b in BOUTONS_CREDITS:
                    b.gerer_evenement(event)
            elif ETAT == "REGLES":
                for b in BOUTONS_REGLES:
                    b.gerer_evenement(event)
            elif ETAT == "JEU":
                changement = scene_jeu.gerer_evenement(event)
                if changement == "PAUSE":
                    ETAT = "PAUSE"
            elif ETAT == "GAMEOVER":
                for b in BOUTONS_GAMEOVER:
                    b.gerer_evenement(event)

        # 2) Affichage
        if ETAT == "MENU":
            dessiner_menu(ECRAN, BOUTONS_MENU)
        elif ETAT == "PAUSE":
            scene_jeu.decompte_dt()
            dessiner_menu(ECRAN, BOUTONS_PAUSE)
        elif ETAT == "CREDITS":
            dessiner_credits(ECRAN, POLICE, WINDOW_WIDTH)
            # Dessine le bouton Retour
            for b in BOUTONS_CREDITS:
                b.dessiner(ECRAN)
        elif ETAT == "REGLES":
            afficher_regles(ECRAN, POLICE, WINDOW_WIDTH)
            for b in BOUTONS_REGLES:
                b.dessiner(ECRAN)
        elif ETAT == "JEU":
            scene_jeu.dessiner(ECRAN)
            # Détection Game Over
            try:
                if getattr(scene_jeu.joueur, "point_de_vie", 1) <= 0:
                    ETAT = "GAMEOVER"
            except Exception:
                pass
        elif ETAT == "GAMEOVER":
            # fige le temps de jeu côté Game
            scene_jeu.decompte_dt()
            dessiner_gameover(ECRAN, BOUTONS_GAMEOVER)

        # 3) Mise à jour de l'écran + FPS
        pygame.display.flip()
        HORLOGE.tick(FPS)


if __name__ == "__main__":
    main()

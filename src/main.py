import sys
import pygame
import os

from classes.menu import creer_boutons_menu, creer_boutons_credits, dessiner_menu, dessiner_credits
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

LARGEUR, HAUTEUR = 1168, 768
ECRAN = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Tower Defense")

POLICE = pygame.font.Font(None, 50)
HORLOGE = pygame.time.Clock()

# Etats possibles: "MENU", "JEU", "PAUSE", "CREDITS"
ETAT = "MENU"

# Gestion du son (muet ou non)
est_muet = False
VOLUME_MUSIQUE = 1.0  # volume par défaut quand non muet

# ------------------- MUSIQUE DE FOND -------------------

def demarrer_musique_de_fond() -> None:
    """Tente de charger et jouer une musique en boucle si le mixer est dispo.
    Le chemin est résolu depuis la racine du projet pour éviter les erreurs de chemin relatifs.
    """
    if not MIXER_DISPONIBLE:
        return
    # Résout le chemin par rapport au dossier racine du projet (src/..)
    base_dir = os.path.dirname(os.path.dirname(__file__))
    pistes_candidates = [
        os.path.join(base_dir, "assets", "audio", "music_Glorious_Morning_by_Waterflame.mp3"),
    ]
    for chemin in pistes_candidates:
        try:
            if not os.path.exists(chemin):
                # fichier absent, passe au suivant
                continue
            pygame.mixer.music.load(chemin)
            pygame.mixer.music.set_volume(0.0 if est_muet else VOLUME_MUSIQUE)
            pygame.mixer.music.play(-1)  # -1 => boucle infinie
            print(f"Musique chargée: {chemin}")
            return
        except Exception as e:
            print(f"Impossible de charger la musique {chemin}: {e}")
            continue
    # Si aucune piste trouvée/chargée, on ignore silencieusement
    return

# Lancer la musique au démarrage
demarrer_musique_de_fond()

# ------------------- CALLBACKS D'ACTION -------------------

def demarrer_jeu():
    global ETAT
    ETAT = "JEU"


def reprendre_jeu():
    global ETAT
    ETAT = "JEU"


def afficher_credits():
    global ETAT
    ETAT = "CREDITS"


def basculer_muet():
    global est_muet
    est_muet = not est_muet
    # Met le volume musique à 0 si muet, sinon remet le volume normal
    if MIXER_DISPONIBLE:
        pygame.mixer.music.set_volume(0.0 if est_muet else VOLUME_MUSIQUE)
    print("Muet activé" if est_muet else "Son activé")


def retour_menu():
    global ETAT
    ETAT = "MENU"


def quitter_jeu():
    """Ferme proprement Pygame et le programme."""
    pygame.quit()
    sys.exit()

# ------------------- CONSTRUCTION DES ÉCRANS -------------------

# Game (scène)
scene_jeu = Game(POLICE)

# Menus (listes de boutons), on génère à partir des callbacks ci-dessus
ACTIONS_MENU_PRINCIPAL = {
    "jouer": demarrer_jeu,
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

BOUTONS_MENU = creer_boutons_menu(POLICE, reprendre=False, actions=ACTIONS_MENU_PRINCIPAL)
BOUTONS_PAUSE = creer_boutons_menu(POLICE, reprendre=True, actions=ACTIONS_MENU_PAUSE)
BOUTONS_CREDITS = creer_boutons_credits(POLICE, action_retour=retour_menu)

# ------------------- BOUCLE PRINCIPALE -------------------

def main() -> None:
    global ETAT

    while True:
        # 1) Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if ETAT == "MENU":
                for b in BOUTONS_MENU:
                    b.gerer_evenement(event)
            elif ETAT == "PAUSE":
                for b in BOUTONS_PAUSE:
                    b.gerer_evenement(event)
            elif ETAT == "CREDITS":
                for b in BOUTONS_CREDITS:
                    b.gerer_evenement(event)
            elif ETAT == "JEU":
                changement = scene_jeu.gerer_evenement(event)
                if changement == "PAUSE":
                    ETAT = "PAUSE"
            

        # 2) Affichage
        if ETAT == "MENU":
            dessiner_menu(ECRAN, BOUTONS_MENU)
        elif ETAT == "PAUSE":
            dessiner_menu(ECRAN, BOUTONS_PAUSE)
        elif ETAT == "CREDITS":
            dessiner_credits(ECRAN, POLICE, LARGEUR)
            # Dessine le bouton Retour
            for b in BOUTONS_CREDITS:
                b.dessiner(ECRAN)
        elif ETAT == "JEU":
            scene_jeu.dessiner(ECRAN)


        # 3) Mise à jour de l'écran + FPS
        pygame.display.flip()
        HORLOGE.tick(60)


if __name__ == "__main__":
    main()
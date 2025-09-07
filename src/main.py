import sys

import pygame

from classes.constants import FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from game import Game
from managers.state_manager import StateManager


def main() -> None:
    """Fonction principale du jeu."""
    # ------------------- INITIALISATION -------------------
    pygame.init()
    
    # Configuration de l'écran
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Protect The Castle")
    
    # Configuration de la police et de l'horloge
    police = pygame.font.Font(None, 50)
    clock = pygame.time.Clock()
    
    # ------------------- INITIALISATION DU JEU -------------------
    # Création de l'instance de jeu
    game = Game(police, est_muet=False)
    
    # Démarrer la musique de fond
    game.audio_manager.demarrer_musique_de_fond()
    
    # Création du gestionnaire d'états
    state_manager = StateManager(police, game)
    
    # ------------------- BOUCLE PRINCIPALE -------------------
    running = True
    while running:
        # 1) Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                state_manager.handle_event(event)
        
        # 2) Mise à jour de l'état
        state_manager.update()
        
        # 3) Affichage
        state_manager.render(screen)
        
        # 4) Mise à jour de l'écran + FPS
        pygame.display.flip()
        clock.tick(FPS)
    
    # Nettoyage
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
import pygame
from .position import Position

class Pointeur:
    def __init__(self):
        self.position = Position(0, 0) 
        self.rayon = 100
        self.couleur = (0, 200, 255)  # couleur magique cyan
        self.surface = None  # Sera créé dynamiquement

    def creer_halo(self, rayon, couleur):
        """Crée un cercle avec halo """
        surface = pygame.Surface((rayon*2, rayon*2), pygame.SRCALPHA)
        # Dessine des cercles concentriques pour créer un effet de halo
        for i in range(rayon, 0, -1):
            alpha = int(80 * (i / rayon)) 
            pygame.draw.circle(surface, (*couleur, alpha), (rayon, rayon), i)
        return surface

    def draw(self, screen, game=None):
        # Récupère la position de la souris
        x, y = pygame.mouse.get_pos()
        self.position.x = x
        self.position.y = y
        
        # Détermine le rayon selon le sort de vision
        rayon = 100  # rayon de base
        if game and hasattr(game, 'sorts') and 'vision' in game.sorts:
            rayon = game.sorts['vision'].portee
        
        # Crée le halo avec le bon rayon
        if self.surface is None or self.rayon != rayon:
            self.rayon = rayon
            self.surface = self.creer_halo(self.rayon, self.couleur)
        
        # Dessine le halo
        if self.surface:
            screen.blit(self.surface, (x - self.rayon, y - self.rayon))

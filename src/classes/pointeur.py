import pygame
from .position import Position

class Pointeur:
    def __init__(self):
        self.position = Position(0, 0) 
        self.rayon = 100
        self.couleur = (0, 200, 255)  # couleur magique cyan
        self.surface = self.creer_halo(self.rayon, self.couleur)

    def creer_halo(self, rayon, couleur):
        """Crée un cercle avec halo """
        surface = pygame.Surface((rayon*2, rayon*2), pygame.SRCALPHA)
        # Dessine des cercles concentriques pour créer un effet de halo
        for i in range(rayon, 0, -1):
            alpha = int(80 * (i / rayon)) 
            pygame.draw.circle(surface, (*couleur, alpha), (rayon, rayon), i)
        return surface

    def draw(self, screen):
        # Récupère la position de la souris
        x, y = pygame.mouse.get_pos()
        self.position.x = x
        self.position.y = y

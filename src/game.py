import pygame

# ------------------- GAME (SCÈNE DE JEU) -------------------
class Game:
    """
    Contient la logique principale de la scène de jeu.
    - police: police pour les textes temporaires
    """
    def __init__(self, police: pygame.font.Font):
        self.police = police

    def dessiner(self, ecran: pygame.Surface) -> None:
        """Dessine la scène de jeu (placeholder à remplacer par la vraie logique)."""
        ecran.fill((50, 100, 50))
        texte = self.police.render("Jeu Tower Defense en cours...", True, (255, 255, 255))
        ecran.blit(texte, (100, 100))

    def gerer_evenement(self, event: pygame.event.Event) -> str | None:
        """
        Gère les événements spécifiques au jeu.
        Retourne une chaîne d'état si un changement est demandé (ex: "PAUSE"), sinon None.
        """
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "PAUSE"
        return None 
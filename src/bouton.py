import pygame

# ------------------- CLASSE BOUTON -------------------
class Bouton:
    """
    Représente un bouton cliquable.
    - texte: texte affiché dans le bouton
    - rect: zone cliquable (pygame.Rect)
    - action: fonction à appeler lorsque le bouton est cliqué
    - police: police utilisée pour dessiner le texte
    - couleurs: dictionnaire pour les couleurs (fond_normal, fond_survol, contour, texte)
    """
    def __init__(self, texte: str, x: int, y: int, largeur: int, hauteur: int, action, police: pygame.font.Font, couleurs: dict):
        self.texte = texte
        self.rect = pygame.Rect(x, y, largeur, hauteur)
        self.action = action
        self.police = police
        self.couleurs = {
            "fond_normal": couleurs.get("fond_normal", (255, 255, 255)),
            "fond_survol": couleurs.get("fond_survol", (200, 200, 200)),
            "contour": couleurs.get("contour", (0, 0, 0)),
            "texte": couleurs.get("texte", (0, 0, 0)),
        }

    def dessiner(self, ecran: pygame.Surface) -> None:
        """Dessine le bouton et gère la couleur de survol."""
        position_souris = pygame.mouse.get_pos()
        survole = self.rect.collidepoint(position_souris)
        couleur_fond = self.couleurs["fond_survol"] if survole else self.couleurs["fond_normal"]

        # Dessine le fond et le contour
        pygame.draw.rect(ecran, couleur_fond, self.rect)
        pygame.draw.rect(ecran, self.couleurs["contour"], self.rect, 3)

        # Dessine le texte centré
        surface_texte = self.police.render(self.texte, True, self.couleurs["texte"])
        ecran.blit(surface_texte, surface_texte.get_rect(center=self.rect.center))

    def gerer_evenement(self, event: pygame.event.Event) -> None:
        """
        Détecte un clic gauche dans la zone du bouton et exécute l'action.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if callable(self.action):
                    self.action() 
import pygame
import os

from classes.pointeur import Pointeur
from classes.ennemi import Gobelin

# ------------------- GAME (SCÈNE DE JEU) -------------------
class Game:
    """
    Contient la logique principale de la scène de jeu.
    - police: police pour les textes temporaires
    """
    def __init__(self, police: pygame.font.Font):
        self.police = police
        
        # Configuration de la carte (768x768)
        self.taille_case = 64  # pixels par case (12x12 cases)
        self.colonnes = 12
        self.lignes = 12
        
        # Surbrillance de case
        self.case_survolee = None
        self.dt = pygame.time.Clock().tick(60) / 1000.0
        
        # Chargement de la carte
        self.carte = self.charger_carte()
        
        # Couleurs
        self.couleur_surbrillance = (255, 255, 0)  # Jaune

        self.pointeur = Pointeur()  # Initialisation du pointeur de souris

        # ---------- ENNEMIS ----------
        tmj_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "tilesets", "carte.tmj")
        gob = Gobelin(id=1, tmj_path=tmj_path)   # charge le chemin depuis la map
        gob.apparaitre()                         # positionné au début du chemin
        self.ennemis = [gob]                     # liste d'ennemis
        
    def charger_carte(self):
        """Charge la carte depuis assets/tilesets/carte.png (chemin résolu depuis la racine du projet)."""
        try:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            chemin_carte = os.path.join(base_dir, "assets", "tilesets", "carte.png")
            if os.path.exists(chemin_carte):
                carte = pygame.image.load(chemin_carte).convert_alpha()
                print(f"Carte chargée: {chemin_carte}")
                return carte
            else:
                raise FileNotFoundError(f"Carte non trouvée: {chemin_carte}")
        except Exception as e:
            print(f"Erreur lors du chargement de la carte: {e}")
            raise
    
    def obtenir_position_case(self, pos_souris):
        x_case = pos_souris[0] // self.taille_case
        y_case = pos_souris[1] // self.taille_case
        if 0 <= x_case < self.colonnes and 0 <= y_case < self.lignes:
            return (x_case, y_case)
        return None
    
    def dessiner_carte(self, ecran: pygame.Surface) -> None:
        if self.carte:
            ecran.blit(self.carte, (0, 0))
        else:
            ecran.fill((50, 100, 50))
    
    def dessiner_surbrillance(self, ecran: pygame.Surface) -> None:
        if not self.case_survolee:
            return
        x_case, y_case = self.case_survolee
        rect = pygame.Rect(
            x_case * self.taille_case,
            y_case * self.taille_case,
            self.taille_case,
            self.taille_case,
        )
        overlay = pygame.Surface((self.taille_case, self.taille_case), pygame.SRCALPHA)
        overlay.fill((*self.couleur_surbrillance, 80))
        ecran.blit(overlay, rect)

    def dessiner_ennemis(self, ecran: pygame.Surface):
        for e in self.ennemis:
            if not e.visible or e.estMort():
                continue
            # cercle (point) vert pour le gobelin
            pygame.draw.circle(ecran, (0, 200, 0), (int(e.position.x), int(e.position.y)), 8)
    
    def dessiner(self, ecran: pygame.Surface) -> None:
        self.dessiner_carte(ecran)
        self.dessiner_surbrillance(ecran)
        self.dessiner_ennemis(ecran)
        self.pointeur.draw(ecran)  # au-dessus
        self.maj(self.dt) 

    
    def maj(self, dt: float):
        # dt en secondes
        for e in self.ennemis:
            e.seDeplacer(dt)
    
    def gerer_evenement(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "PAUSE"
        if event.type == pygame.MOUSEMOTION:
            self.case_survolee = self.obtenir_position_case(pygame.mouse.get_pos())
        return None
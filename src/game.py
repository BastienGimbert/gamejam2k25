import pygame
import os

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
        
        # Chargement de la carte
        self.carte = self.charger_carte()
        
        # Couleurs
        self.couleur_quadrillage = (100, 100, 100)
        self.couleur_surbrillance = (255, 255, 0)  # Jaune
        
    def charger_carte(self):
        """Charge la carte depuis assets/tilesets/carte.png (chemin résolu depuis la racine du projet)."""
        try:
            # Résout le chemin par rapport au dossier racine du projet (src/..)
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
        """Convertit la position de la souris en coordonnées de case"""
        x_case = pos_souris[0] // self.taille_case
        y_case = pos_souris[1] // self.taille_case
        if 0 <= x_case < self.colonnes and 0 <= y_case < self.lignes:
            return (x_case, y_case)
        return None
    
    def dessiner_quadrillage(self, ecran: pygame.Surface) -> None:
        """Dessine le quadrillage de la carte"""
        largeur = self.colonnes * self.taille_case
        hauteur = self.lignes * self.taille_case
        for x in range(0, largeur + 1, self.taille_case):
            pygame.draw.line(ecran, self.couleur_quadrillage, (x, 0), (x, hauteur))
        for y in range(0, hauteur + 1, self.taille_case):
            pygame.draw.line(ecran, self.couleur_quadrillage, (0, y), (largeur, y))
    
    def dessiner_carte(self, ecran: pygame.Surface) -> None:
        """Dessine la carte de fond"""
        if self.carte:
            # La carte fait déjà 768x768, on l'affiche directement
            ecran.blit(self.carte, (0, 0))
        else:
            ecran.fill((50, 100, 50))
    
    def dessiner_surbrillance(self, ecran: pygame.Surface) -> None:
        """Dessine la surbrillance sur la case survolée"""
        if not self.case_survolee:
            return
        x_case, y_case = self.case_survolee
        rect = pygame.Rect(
            x_case * self.taille_case,
            y_case * self.taille_case,
            self.taille_case,
            self.taille_case,
        )
        # Surface semi-transparente
        overlay = pygame.Surface((self.taille_case, self.taille_case), pygame.SRCALPHA)
        overlay.fill((*self.couleur_surbrillance, 80))
        ecran.blit(overlay, rect)
    
    def dessiner(self, ecran: pygame.Surface) -> None:
        """Dessine la carte, le quadrillage et la surbrillance"""
        self.dessiner_carte(ecran)
        self.dessiner_quadrillage(ecran)
        self.dessiner_surbrillance(ecran)
    
    def gerer_evenement(self, event: pygame.event.Event) -> str | None:
        """Gestion des entrées pour la scène de jeu"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "PAUSE"
        if event.type == pygame.MOUSEMOTION:
            self.case_survolee = self.obtenir_position_case(pygame.mouse.get_pos())
        return None

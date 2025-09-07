import math
import os
from typing import TYPE_CHECKING, Optional, Tuple

import pygame

from classes.constants import ASSETS_DIR
from classes.sprites import charger_image_avec_redimensionnement

if TYPE_CHECKING:
    from game import Game


class UIManager:
    """Manager pour gérer tous les aspects de l'interface utilisateur."""
    
    def __init__(self, game: "Game"):
        self.game = game
        
        # Couleurs UI
        self.couleur_quadrillage = (40, 60, 100)
        self.couleur_surbrillance = (80, 180, 255)
        self.couleur_surbrillance_interdite = (255, 80, 80)
        
        # Cache pour les images
        self._victoire_image = None
    
    def dessiner_quadrillage(self, ecran: pygame.Surface) -> None:
        """Dessine le quadrillage de la grille."""
        largeur_draw = self.game.largeur_ecran
        for x in range(0, largeur_draw + 1, self.game.taille_case):
            pygame.draw.line(
                ecran, self.couleur_quadrillage, (x, 0), (x, self.game.hauteur_ecran)
            )
        for y in range(0, self.game.hauteur_ecran + 1, self.game.taille_case):
            pygame.draw.line(ecran, self.couleur_quadrillage, (0, y), (largeur_draw, y))
    
    def dessiner_surbrillance(self, ecran: pygame.Surface) -> None:
        """Dessine les surbrillances (tours, éclair, etc.)."""
        # Surbrillance pour l'éclair (seulement sur les cases du chemin, sauf les 6 en haut à gauche)
        if (
            hasattr(self.game, "eclair_selectionne")
            and self.game.eclair_selectionne
            and self.game.case_survolee
        ):
            if self.game.case_survolee in getattr(
                self.game, "cases_bannies", set()
            ) and self.game.case_survolee not in [
                (x, y) for y in (0, 1) for x in range(0, 6)
            ]:
                x_case, y_case = self.game.case_survolee
                rect = pygame.Rect(
                    x_case * self.game.taille_case,
                    y_case * self.game.taille_case,
                    self.game.taille_case,
                    self.game.taille_case,
                )
                overlay = pygame.Surface(
                    (self.game.taille_case, self.game.taille_case), pygame.SRCALPHA
                )
                # Couleur jaune pour l'éclair
                overlay.fill((255, 255, 0, 100))
                if rect.right <= self.game.largeur_ecran:
                    ecran.blit(overlay, rect)
            return

        # Surbrillance pour les tours
        if not self.game.case_survolee or not self.game.type_selectionne:
            return

        x_case, y_case = self.game.case_survolee
        rect = pygame.Rect(
            x_case * self.game.taille_case,
            y_case * self.game.taille_case,
            self.game.taille_case,
            self.game.taille_case,
        )

        # Surbrillance
        overlay = pygame.Surface((self.game.taille_case, self.game.taille_case), pygame.SRCALPHA)
        interdit = (x_case, y_case) in getattr(self.game, "cases_bannies", set()) or (
            x_case,
            y_case,
        ) in self.game.tour_manager.positions_occupees
        couleur = (
            self.couleur_surbrillance_interdite
            if interdit
            else self.couleur_surbrillance
        )
        overlay.fill((*couleur, 80))
        if rect.right <= self.game.largeur_ecran:
            ecran.blit(overlay, rect)

        # Cercle autour de la case
        portee = self.game.tour_manager.portee_par_type.get(self.game.type_selectionne, 0)
        cx = x_case * self.game.taille_case + self.game.taille_case // 2
        cy = y_case * self.game.taille_case + self.game.taille_case // 2

        # Dessine un cercle
        dash_count = 15  # nombre de segments
        dash_length = 0.15  # en radians

        for i in range(dash_count):
            angle_start = 2 * math.pi * i / dash_count
            angle_end = angle_start + dash_length
            x1 = int(cx + portee * math.cos(angle_start))
            y1 = int(cy + portee * math.sin(angle_start))
            x2 = int(cx + portee * math.cos(angle_end))
            y2 = int(cy + portee * math.sin(angle_end))
            pygame.draw.line(ecran, (255, 255, 255), (x1, y1), (x2, y2), 3)
    
    def dessiner_effet_nuit(self, ecran: pygame.Surface, dt: float) -> None:
        """Dessine l'effet de nuit avec les lumières."""
        if not self.game.ennemi_manager.est_nuit:
            return
        
        nuit_surface = pygame.Surface(
            (self.game.largeur_ecran, self.game.hauteur_ecran), pygame.SRCALPHA
        )
        nuit_surface.fill((0, 6, 25, int(255 * 0.7)))  # 70% opacity

        # Vérifier si la fée est active
        if "fee" in self.game.sorts and self.game.sorts["fee"].est_actif():
            # Si la fée est active, éclairer toute la carte
            pygame.draw.circle(
                nuit_surface,
                (0, 0, 0, 0),
                (self.game.largeur_ecran // 2, self.game.hauteur_ecran // 2),
                max(self.game.largeur_ecran, self.game.hauteur_ecran),
            )
        else:
            # Effet de lumière du curseur seulement si la souris est sur la carte
            x, y = pygame.mouse.get_pos()
            if x < self.game.largeur_ecran:
                # Portée de base du curseur
                portee_curseur = 100
                # Vérifier si le joueur a le sort de vision et augmenter la portée
                if "vision" in self.game.sorts:
                    portee_curseur = self.game.sorts["vision"].portee
                pygame.draw.circle(
                    nuit_surface, (0, 0, 0, 0), (x, y), portee_curseur
                )  # dessin de la lumiere
        
        # Mettre à jour les feux de camp
        self.game.tour_manager.mettre_a_jour_feux_de_camps(dt, nuit_surface)

        ecran.blit(nuit_surface, (0, 0))
    
    def dessiner_victoire(self, ecran: pygame.Surface) -> None:
        """Dessine l'écran de victoire."""
        if self._victoire_image is None:
            self._victoire_image = charger_image_avec_redimensionnement(
                "assets/VICTOIRE.png", 
                (ecran.get_width(), ecran.get_height())
            )
        
        if self._victoire_image:
            ecran.blit(self._victoire_image, (0, 0))
    
    def dessiner_effets_sorts(self, ecran: pygame.Surface) -> None:
        """Dessine les effets visuels des sorts."""
        for sort in self.game.sorts.values():
            sort.dessiner_effet(ecran, self.game)
    
    def dessiner_interface_jeu(self, ecran: pygame.Surface, dt: float) -> None:
        """Dessine l'interface de jeu complète."""
        # Dessiner la carte de base
        ecran.blit(self.game.carte, (0, 0))
        
        # Dessiner les tours
        self.game.tour_manager.dessiner_tours_placees(ecran, self.game.taille_case)
        self.game.tour_manager.dessiner_personnages_tours(ecran)
        
        # Dessiner les surbrillances
        self.dessiner_surbrillance(ecran)
        
        # Dessiner l'effet de nuit
        self.dessiner_effet_nuit(ecran, dt)
        
        # Dessiner les boutiques
        self.game.shop_manager.dessiner_boutique_tours(ecran)
        self.game.shop_manager.dessiner_boutique_sorts(ecran)
        
        # Dessiner les ennemis
        self.game.ennemi_manager.dessiner_ennemis(ecran)
        
        # Dessiner les effets des sorts
        self.dessiner_effets_sorts(ecran)
        
        # Dessiner les projectiles et effets d'explosion
        self.game.tour_manager.dessiner_projectiles(ecran)
        self.game.tour_manager.dessiner_effets_explosion(ecran)
    
    def nettoyer_cache(self) -> None:
        """Nettoie le cache des images."""
        self._victoire_image = None

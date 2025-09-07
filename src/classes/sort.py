import math
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from classes.constants import ASSETS_DIR
from classes.sprites import charger_image_assets, decouper_sprite
import os

import pygame

if TYPE_CHECKING:
    from game import Game


class Sort(ABC):
    """Classe de base pour tous les sorts avec système de niveaux."""

    def __init__(self, nom: str, niveau: int = 1):
        self.nom = nom
        self.niveau = niveau
        self.prix_base = 30  # Prix de base pour le niveau 1

    @property
    def prix(self) -> int:
        """Calcule le prix du sort selon son niveau (niveau * prix_base)."""
        return self.niveau * self.prix_base

    @property
    def nom_complet(self) -> str:
        """Retourne le nom complet avec le niveau (ex: "Vision 3")."""
        return f"{self.nom} {self.niveau}"

    def peut_etre_achete(self, argent_joueur: int) -> bool:
        """Vérifie si le joueur a assez d'argent pour acheter ce sort."""
        return argent_joueur >= self.prix

    def acheter(self, joueur) -> bool:
        """Achète le sort et augmente son niveau. Retourne True si l'achat a réussi."""
        if self.peut_etre_achete(joueur.argent):
            joueur.argent -= self.prix
            self.niveau += 1
            return True
        return False

    @abstractmethod
    def appliquer_effet(self, game: "Game") -> None:
        """Applique l'effet du sort au jeu."""
        pass

    @abstractmethod
    def dessiner_effet(self, ecran: pygame.Surface, game: "Game") -> None:
        """Dessine l'effet visuel du sort."""
        pass


class SortVision(Sort):
    """Sort qui augmente la portée de visibilité autour du curseur."""

    def __init__(self, niveau: int = 1):
        super().__init__("Vision", niveau)
        self.portee_base = 100  # Portée de base du curseur
        self.max_niveau = 3  # Maximum 3 niveaux

    @property
    def portee(self) -> int:
        """Calcule la portée de vision selon le niveau."""
        if self.niveau == 1:
            return int(self.portee_base * 1.0) 
        elif self.niveau == 2:
            return int(self.portee_base * 1.25)  # +25%
        elif self.niveau >= 3:
            return int(self.portee_base * 1.5)  # +50%
        return self.portee_base

    @property
    def nom_complet(self) -> str:
        """Retourne le nom complet avec le niveau (Vision 1, Vision 2, Vision Max)."""
        if self.niveau == 1:
            return "Vision 1"
        elif self.niveau == 2:
            return "Vision 2"
        elif self.niveau >= 3:
            return "Vision Max"
        return f"Vision {self.niveau}"

    def est_au_niveau_maximum(self) -> bool:
        """Retourne True si le sort est au niveau maximum."""
        return self.niveau >= self.max_niveau

    def acheter(self, joueur) -> bool:
        """Achète le sort et augmente son niveau. Retourne True si l'achat a réussi."""
        if self.peut_etre_achete(joueur.argent) and self.niveau < self.max_niveau:
            joueur.argent -= self.prix
            self.niveau += 1
            return True
        return False

    def appliquer_effet(self, game: "Game") -> None:
        """Met à jour la visibilité des ennemis selon la portée du sort."""
        # On utilise le système existant mais avec une portée augmentée
        # Le travail est fait dans majVisible modifié des ennemis
        pass

    def dessiner_effet(self, ecran: pygame.Surface, game: "Game") -> None:
        """N'affiche pas d'effet visuel - utilise l'effet de lumière existant du jeu."""
        # L'effet de lumière est géré par le système existant dans le jeu
        # On ne dessine rien ici pour garder l'effet de lumière original
        pass


class SortFee(Sort):
    """Sort de la fée qui éclaire toute la carte pendant 5 secondes."""

    def __init__(self, niveau: int = 1):
        super().__init__("Fee", niveau)
        self.prix_base = 30  
        self.duree_eclairage = 5.0  # en sec
        self.temps_debut = None  # Timestamp du début de l'effet
        self.actif = False  
        self.max_niveau = 1  # Un seul niveau pour ce sort

    @property
    def prix(self) -> int:
        return self.prix_base

    @property
    def nom_complet(self) -> str:
        """Retourne le nom complet du sort."""
        return "Fée"

    def peut_etre_achete(self, argent_joueur: int) -> bool:
        """Vérifie si le joueur a assez d'argent ET que l'effet n'est pas déjà actif."""
        return argent_joueur >= self.prix and not self.actif

    def est_au_niveau_maximum(self) -> bool:
        """Retourne False car ce sort n'a pas de niveau maximum (on peut toujours le racheter)."""
        return False

    def acheter(self, joueur) -> bool:
        """Achète le sort et active l'effet d'éclairage."""
        if self.peut_etre_achete(joueur.argent):
            joueur.argent -= self.prix
            self.activer_effet()
            return True
        return False

    def activer_effet(self) -> None:
        """Active l'effet d'éclairage de la fée."""
        self.actif = True
        self.temps_debut = pygame.time.get_ticks() / 1000.0  # Conversion en secondes

    def est_actif(self) -> bool:
        """Vérifie si l'effet est encore actif."""
        if not self.actif or self.temps_debut is None:
            return False

        temps_ecoule = (pygame.time.get_ticks() / 1000.0) - self.temps_debut
        if temps_ecoule >= self.duree_eclairage:
            self.actif = False
            return False

        return True

    def appliquer_effet(self, game: "Game") -> None:
        """Applique l'effet d'éclairage - rend tous les ennemis visibles."""
        if self.est_actif():
            # Rendre tous les ennemis visibles pendant l'effet
            for ennemi in game.ennemi_manager.get_ennemis_actifs():
                ennemi.set_visibilite(True)
        # Ne pas forcer l'invisibilité - laisser la logique normale de majVisible s'en occuper

    def dessiner_effet(self, ecran: pygame.Surface, game: "Game") -> None:
        """N'affiche pas d'effet visuel - utilise le système d'éclairage existant."""
        # L'effet d'éclairage est géré par le système existant dans le jeu
        # On ne dessine rien ici pour garder l'effet de lumière original
        pass


class SortEclair(Sort):
    """Sort d'éclair qui inflige 10 dégâts aux ennemis sur une case cliquée."""

    _frames: list[pygame.Surface] | None = None


    def __init__(self, niveau: int = 1):
        super().__init__("Eclair", niveau)
        self.prix_base = 30
        self.degats = 10  # Dégâts
        self.max_niveau = 1  # Un seul niveau pour ce sort
        self.case_cible = None  # Case ciblée 
        self.temps_activation = None  # Timestamp de l'activation
        self.duree_effet = 0.6  # en sec

        if SortEclair._frames is None:
            sheet = charger_image_assets("lightning.png", "spell")
            if sheet:
                SortEclair._frames = decouper_sprite(sheet, 10, horizontal=True, copy=True)
            else:
                SortEclair._frames = []

    @property
    def prix(self) -> int:
        """Prix fixe de 80 gold."""
        return self.prix_base

    @property
    def nom_complet(self) -> str:
        """Retourne le nom complet du sort."""
        return "Eclair"

    def peut_etre_achete(self, argent_joueur: int) -> bool:
        """Vérifie si le joueur a assez d'argent pour acheter ce sort."""
        return argent_joueur >= self.prix

    def est_au_niveau_maximum(self) -> bool:
        """Retourne False car ce sort n'a pas de niveau maximum (on peut toujours le racheter)."""
        return False

    def activer_sur_case(self, case_x: int, case_y: int) -> bool:
        """Active l'éclair sur une case spécifique. Retourne True si l'activation a réussi."""
        if self.case_cible is not None:
            return False  # Déjà en cours d'activation

        self.case_cible = (case_x, case_y)
        self.temps_activation = pygame.time.get_ticks() / 1000.0

        return True

    def est_actif(self) -> bool:
        """Vérifie si l'effet d'éclair est encore actif."""
        if self.case_cible is None or self.temps_activation is None:
            return False

        temps_ecoule = (pygame.time.get_ticks() / 1000.0) - self.temps_activation
        if temps_ecoule >= self.duree_effet:
            self.case_cible = None
            self.temps_activation = None
            return False

        return True

    def appliquer_effet(self, game: "Game") -> None:
        """Applique les dégâts de l'éclair aux ennemis sur la case ciblée."""
        if self.est_actif() and self.case_cible:
            case_x, case_y = self.case_cible
            taille_case = 64  # Taille d'une case en pixels

            # Calculer la zone de la case en pixels
            x_min = case_x * taille_case
            x_max = (case_x + 1) * taille_case
            y_min = case_y * taille_case
            y_max = (case_y + 1) * taille_case

            # Infliger des dégâts aux ennemis dans cette zone
            for ennemi in game.ennemi_manager.get_ennemis_actifs():
                if (
                    x_min <= ennemi.position.x <= x_max
                    and y_min <= ennemi.position.y <= y_max
                ):
                    ennemi.perdreVie(self.degats)

    def dessiner_effet(self, ecran: pygame.Surface, game: "Game") -> None:
        if self.est_actif() and self.case_cible:
            case_x, case_y = self.case_cible
            taille_case = 64
            x_pos, y_pos = case_x * taille_case, case_y * taille_case

            # --- Animation lightning ---
            temps_ecoule = (pygame.time.get_ticks() / 1000.0) - self.temps_activation
            progress = temps_ecoule / self.duree_effet
            frame_index = int(progress * len(SortEclair._frames))
            frame_index = min(frame_index, len(SortEclair._frames) - 1)
            frame = SortEclair._frames[frame_index]

            # Appliquer une échelle verticale pour étirer l’éclair
            scale_factor_y = 2.0  # Facteur d'échelle vertical
            new_w = frame.get_width()
            new_h = int(frame.get_height() * scale_factor_y)
            frame = pygame.transform.scale(frame, (new_w, new_h))

            # Centrer l’éclair sur la case
            vertical_offset = -80 * scale_factor_y
            rect = frame.get_rect(center=(x_pos + taille_case // 2, y_pos + taille_case // 2 + vertical_offset))
            ecran.blit(frame, rect)

            # --- Éclaircissement blanc en overlay (déjà existant) ---
            alpha = int(255 * (1 - progress))
            alpha = max(0, min(255, alpha))
            eclairage_surface = pygame.Surface((taille_case, taille_case), pygame.SRCALPHA)
            eclairage_surface.fill((255, 255, 255, alpha))
            ecran.blit(eclairage_surface, (x_pos, y_pos))


from abc import ABC, abstractmethod
from math import atan2, degrees, hypot
from typing import TYPE_CHECKING, ClassVar, Optional

import pygame

from classes.ennemi import Chevalier, Ennemi
from classes.position import Position

if TYPE_CHECKING:
    from game import Game


class Projectile(ABC):
    """Base abstraite d'un projectile (position, direction, mouvement, collision)."""

    def __init__(
        self,
        origine: Position,
        cible_pos: Position,
        degats: int,
        vitesse: float,
        rayon_collision: float,
        portee_max: Optional[float] = 800.0,
    ) -> None:
        # Position courante
        self.x = float(origine.x)
        self.y = float(origine.y)
        self.position = Position(self.x, self.y)

        # Caractéristiques
        self.degats = int(degats)
        self.vitesse = float(vitesse)
        self.rayon_collision = float(rayon_collision)
        self.portee_max = float(portee_max) if portee_max is not None else None

        # Direction figée à l'instant du tir (normalisée)
        dx = float(cible_pos.x) - self.x
        dy = float(cible_pos.y) - self.y
        distance = max(1e-6, hypot(dx, dy))
        self.vx = self.vitesse * dx / distance
        self.vy = self.vitesse * dy / distance

        # Ciblage dynamique (optionnel): si défini, on suivra l'ennemi en temps réel
        self.cible: Optional[Ennemi] = None

        # Suivi
        self._distance_parcourue = 0.0
        self.detruit = False

        # Chemin d'image par défaut (défini dans les sous-classes)
        # Chemin relatif depuis la racine du projet, ex: "assets/.../1.png"
        # Utilisé par le jeu pour charger l'image automatiquement
        # via une fonction générique.

    def _angle_degres(self) -> float:
        # 0° = droite, 90° = haut (sens anti-horaire)
        return (degrees(atan2(self.vy, self.vx)) + 360.0) % 360.0

    def mettreAJour(self, dt: float) -> None:
        if self.detruit:
            return
        # Si une cible est assignée, recalculer la direction pour viser en continu
        if self.cible is not None and not self.cible.estMort():
            dx = float(self.cible.position.x) - self.x
            dy = float(self.cible.position.y) - self.y
            dist = max(1e-6, hypot(dx, dy))
            self.vx = self.vitesse * dx / dist
            self.vy = self.vitesse * dy / dist
        dx = self.vx * dt
        dy = self.vy * dt
        self.x += dx
        self.y += dy
        self._distance_parcourue += hypot(dx, dy)
        if self.portee_max is not None and self._distance_parcourue >= self.portee_max:
            self.detruit = True

    def aTouche(self, e: Ennemi) -> bool:
        if e.estMort():
            return False
        ex, ey = e.position.x, e.position.y
        return hypot(self.x - ex, self.y - ey) <= self.rayon_collision

    def appliquerDegats(self, e: Ennemi) -> None:
        e.perdreVie(self.degats)
        self.detruit = True

    @abstractmethod
    def dessiner(self, ecran: pygame.Surface) -> None:
        pass


class ProjectileFleche(Projectile):
    """Flèche: rapide, dégâts fixes = 20."""

    CHEMIN_IMAGE: ClassVar[str] = "tower/archer/Arrow/1.png"

    def __init__(self, origine: Position, cible_pos: Position) -> None:
        super().__init__(
            origine=origine,
            cible_pos=cible_pos,
            degats=20,
            vitesse=720.0,
            rayon_collision=12.0,
        )
        self.image_base: Optional[pygame.Surface] = None

    def dessiner(self, ecran: pygame.Surface) -> None:
        if self.detruit or self.image_base is None:
            return
        angle = self._angle_degres()
        sprite = pygame.transform.rotozoom(self.image_base, 90 - angle, 1.0)
        rect = sprite.get_rect(center=(int(self.x), int(self.y)))
        ecran.blit(sprite, rect)

    def appliquerDegats(self, e: Ennemi) -> None:
        if isinstance(e, Chevalier):
            # Les chevaliers en prennent pas de degats par des fleches
            e.block()
            self.detruit = True
            return
        e.perdreVie(self.degats)
        self.detruit = True


class ProjectilePierre(Projectile):
    """Pierre: lente, dégâts fixes = 70."""

    CHEMIN_IMAGE: ClassVar[str] = "tower/catapulte/projectiles/1.png"

    def __init__(
        self, origine: Position, cible_pos: Position, game_ref: Optional["Game"]
    ) -> None:
        super().__init__(
            origine=origine,
            cible_pos=cible_pos,
            degats=170,
            vitesse=250.0,
            rayon_collision=16.0,
        )
        self.image_base: Optional[pygame.Surface] = None

    def dessiner(self, ecran: pygame.Surface) -> None:
        if self.detruit or self.image_base is None:
            return
        angle = self._angle_degres()
        sprite = pygame.transform.rotozoom(self.image_base, 90 - angle, 1.5)
        rect = sprite.get_rect(center=(int(self.x), int(self.y)))
        ecran.blit(sprite, rect)


# --- Nouveau projectile de tour mage ---
class ProjectileTourMage(Projectile):
    """Projectile de la tour Mage: orbe magique avec dégâts de zone."""

    CHEMIN_IMAGE: ClassVar[str] = "tower/mage/projectiles/1.png"

    def __init__(self, origine: Position, cible_pos: Position) -> None:
        # Moins rapide qu'une flèche, dégâts supérieurs
        super().__init__(
            origine=origine,
            cible_pos=cible_pos,
            degats=40,
            vitesse=400.0,
            rayon_collision=14.0,
        )
        self.image_base: Optional[pygame.Surface] = None
        # Rayon de la zone d'effet (dégâts de zone)
        self.rayon_zone_effet = 60.0

    def dessiner(self, ecran: pygame.Surface) -> None:
        if self.detruit or self.image_base is None:
            return
        angle = self._angle_degres()
        sprite = pygame.transform.rotozoom(self.image_base, 90 - angle, 1.5)
        rect = sprite.get_rect(center=(int(self.x), int(self.y)))
        ecran.blit(sprite, rect)
        
        # Dessiner un cercle de zone d'effet en transparence (optionnel, pour debug)
        # pygame.draw.circle(ecran, (255, 0, 255, 50), (int(self.x), int(self.y)), int(self.rayon_zone_effet), 2)

    def appliquerDegats(self, e: Ennemi) -> None:
        """Applique les dégâts à l'ennemi touché et marque le projectile pour destruction."""
        # Le projectile sera détruit après avoir touché, mais les dégâts de zone
        # seront appliqués dans la méthode spéciale du jeu
        self.detruit = True

    def appliquerDegatsZone(self, ennemis: list[Ennemi]) -> None:
        """Applique les dégâts de zone à tous les ennemis dans le rayon d'effet."""
        for ennemi in ennemis:
            if ennemi.estMort():
                continue
            
            # Calculer la distance entre le point d'impact et l'ennemi
            distance = hypot(self.x - ennemi.position.x, self.y - ennemi.position.y)
            
            # Si l'ennemi est dans la zone d'effet
            if distance <= self.rayon_zone_effet:
                # Appliquer les dégâts complets
                ennemi.perdreVie(self.degats)


class ProjectileMageEnnemi(Projectile):
    """Projectile du mage qui suit un projectile de pierre."""

    CHEMIN_IMAGE: ClassVar[str] = "enemy/mage/Projectile2.png"

    def __init__(
        self, origine: Position, cible_proj: "ProjectilePierre", vitesse: float = 700.0
    ):
        # On initialise avec la position initiale du projectile
        # Portée illimitée pour garantir l'interception, collision un peu plus large
        super().__init__(
            origine=origine,
            cible_pos=Position(cible_proj.x, cible_proj.y),
            degats=0,
            vitesse=vitesse,
            rayon_collision=24.0,
            portee_max=400,
        )
        self.image_base: Optional[pygame.Surface] = None
        self.cible_proj = cible_proj  # On garde la référence pour le guidage

    def mettreAJour(self, dt: float) -> None:
        if self.detruit:
            return
        # recalcul de la direction vers le projectilePierre
        if self.cible_proj is not None and not getattr(
            self.cible_proj, "detruit", True
        ):
            dx = self.cible_proj.x - self.x
            dy = self.cible_proj.y - self.y
            dist = max(1e-6, hypot(dx, dy))
            self.vx = self.vitesse * dx / dist
            self.vy = self.vitesse * dy / dist

        # déplacement
        self.x += self.vx * dt
        self.y += self.vy * dt
        self._distance_parcourue += hypot(self.vx * dt, self.vy * dt)

        # détruit si dépasse la portée max
        if self.portee_max is not None and self._distance_parcourue >= self.portee_max:
            self.detruit = True

        # détruit si la cible est détruite
        if getattr(self.cible_proj, "detruit", False):
            self.detruit = True

    def aTouche(self, p: "ProjectilePierre") -> bool:
        # collision simple cercle → cercle
        if getattr(p, "detruit", True):
            return False
        return hypot(self.x - p.x, self.y - p.y) <= self.rayon_collision

    def dessiner(self, ecran: pygame.Surface) -> None:
        if self.detruit or self.image_base is None:
            return
        angle = self._angle_degres()
        sprite = pygame.transform.rotozoom(self.image_base, 90 - angle, 1.5)
        rect = sprite.get_rect(center=(int(self.x), int(self.y)))
        ecran.blit(sprite, rect)


class EffetExplosion:
    """Effet visuel temporaire pour les explosions de zone."""
    
    def __init__(self, x: float, y: float, rayon: float, duree: float = 0.5):
        self.x = x
        self.y = y
        self.rayon_max = rayon
        self.duree = duree
        self.temps_ecoule = 0.0
        self.actif = True
    
    def mettre_a_jour(self, dt: float) -> None:
        """Met à jour l'effet d'explosion."""
        self.temps_ecoule += dt
        if self.temps_ecoule >= self.duree:
            self.actif = False
    
    def dessiner(self, ecran: pygame.Surface) -> None:
        """Dessine l'effet d'explosion."""
        if not self.actif:
            return
        
        # Calculer le rayon actuel (expansion progressive)
        progress = self.temps_ecoule / self.duree
        rayon_actuel = self.rayon_max * progress
        
        # Calculer l'opacité (diminue avec le temps)
        alpha = int(255 * (1.0 - progress))
        
        # Créer une surface temporaire pour l'effet
        surface_effet = pygame.Surface((int(rayon_actuel * 2), int(rayon_actuel * 2)), pygame.SRCALPHA)
        
        # Dessiner le cercle d'explosion
        pygame.draw.circle(surface_effet, (255, 100, 255, alpha), 
                          (int(rayon_actuel), int(rayon_actuel)), int(rayon_actuel), 3)
        
        # Dessiner un cercle intérieur plus lumineux
        pygame.draw.circle(surface_effet, (255, 200, 255, alpha // 2), 
                          (int(rayon_actuel), int(rayon_actuel)), int(rayon_actuel * 0.7), 2)
        
        # Positionner et afficher l'effet
        rect_effet = surface_effet.get_rect(center=(int(self.x), int(self.y)))
        ecran.blit(surface_effet, rect_effet)

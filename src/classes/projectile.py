from abc import ABC, abstractmethod
from math import atan2, degrees, hypot
from typing import TYPE_CHECKING, ClassVar, Optional

import pygame

from classes.ennemi import Ennemi
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

    CHEMIN_IMAGE: ClassVar[str] = "assets/tower/archer/Arrow/1.png"

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


class ProjectilePierre(Projectile):
    """Pierre: lente, dégâts fixes = 70."""

    CHEMIN_IMAGE: ClassVar[str] = "assets/tower/catapulte/projectiles/1.png"

    def __init__(
        self, origine: Position, cible_pos: Position, game_ref: Optional["Game"]
    ) -> None:
        super().__init__(
            origine=origine,
            cible_pos=cible_pos,
            degats=70,
            vitesse=360.0,
            rayon_collision=16.0,
        )
        self.image_base: Optional[pygame.Surface] = None

    def dessiner(self, ecran: pygame.Surface) -> None:
        if self.detruit or self.image_base is None:
            return
        angle = self._angle_degres()
        sprite = pygame.transform.rotozoom(self.image_base, 90 - angle, 1.0)
        rect = sprite.get_rect(center=(int(self.x), int(self.y)))
        ecran.blit(sprite, rect)


# --- Nouveau projectile de tour mage ---
class ProjectileTourMage(Projectile):
    """Projectile de la tour Mage: orbe magique rapide à dégâts moyens."""

    CHEMIN_IMAGE: ClassVar[str] = "assets/tower/mage/projectiles/1.png"

    def __init__(self, origine: Position, cible_pos: Position) -> None:
        # Moins rapide qu'une flèche, dégâts supérieurs
        super().__init__(
            origine=origine,
            cible_pos=cible_pos,
            degats=40,
            vitesse=600.0,
            rayon_collision=14.0,
        )
        self.image_base: Optional[pygame.Surface] = None

    def dessiner(self, ecran: pygame.Surface) -> None:
        if self.detruit or self.image_base is None:
            return
        angle = self._angle_degres()
        sprite = pygame.transform.rotozoom(self.image_base, 90 - angle, 1.0)
        rect = sprite.get_rect(center=(int(self.x), int(self.y)))
        ecran.blit(sprite, rect)


class ProjectileMageEnnemi(Projectile):
    """Projectile du mage qui suit un projectile de pierre."""

    CHEMIN_IMAGE: ClassVar[str] = "assets/enemy/mage/Projectile2.png"

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
            portee_max=None,
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

        # optionnel : détruit si dépasse la portée max
        if self.portee_max is not None and self._distance_parcourue >= self.portee_max:
            self.detruit = True

        # optionnel : détruit si la cible est détruite
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
        sprite = pygame.transform.rotozoom(self.image_base, 90 - angle, 1.0)
        rect = sprite.get_rect(center=(int(self.x), int(self.y)))
        ecran.blit(sprite, rect)

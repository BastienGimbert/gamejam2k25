from math import atan2, degrees, hypot
from typing import Optional, ClassVar

import pygame
from abc import ABC, abstractmethod

from classes.position import Position
from classes.ennemi import Ennemi


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
    """Flèche: rapide, dégâts fixes = 1."""

    CHEMIN_IMAGE: ClassVar[str] = "assets/tower/archer/Arrow/1.png"

    def __init__(self, origine: Position, cible_pos: Position) -> None:
        super().__init__(origine=origine, cible_pos=cible_pos, degats=1, vitesse=720.0, rayon_collision=12.0)
        self.image_base: Optional[pygame.Surface] = None

    def dessiner(self, ecran: pygame.Surface) -> None:
        if self.detruit or self.image_base is None:
            return
        angle = self._angle_degres()
        rotation = 90.0 - angle
        # 1) Rotation sur image originale pour éviter l'accumulation d'artefacts
        sprite = pygame.transform.rotate(self.image_base, rotation)
        # 2) Mise à l'échelle douce après rotation (meilleure netteté)
        sprite = pygame.transform.smoothscale(sprite, (24, 24))
        rect = sprite.get_rect(center=(int(self.x), int(self.y)))
        ecran.blit(sprite, rect)


class ProjectilePierre(Projectile):
    """Pierre: lente, dégâts fixes = 2."""

    CHEMIN_IMAGE: ClassVar[str] = "assets/tower/catapult/projectiles/1.png"

    def __init__(self, origine: Position, cible_pos: Position) -> None:
        super().__init__(origine=origine, cible_pos=cible_pos, degats=2, vitesse=360.0, rayon_collision=16.0)
        self.image_base: Optional[pygame.Surface] = None

    def dessiner(self, ecran: pygame.Surface) -> None:
        if self.detruit or self.image_base is None:
            return
        angle = self._angle_degres()
        rotation = 90.0 - angle
        sprite = pygame.transform.rotate(self.image_base, rotation)
        sprite = pygame.transform.smoothscale(sprite, (22, 22))
        rect = sprite.get_rect(center=(int(self.x), int(self.y)))
        ecran.blit(sprite, rect)



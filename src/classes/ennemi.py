from typing import Callable, List, Optional
from abc import ABC, abstractmethod
from classes.position import Position
from classes.utils import charger_chemin_tiled, distance_positions, decouper_sprite
import pygame
import os
from time import sleep

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

class Ennemi(ABC):
    def __init__(
        self,
        vitesse: float,
        pointsDeVie: int,
        degats: int,
        tempsApparition = 0,
        chemin: Optional[List[Position]] = None,
        on_reach_castle: Optional[Callable[["Ennemi"], None]] = None,
        tmj_path: str = "assets/tilesets/carte.tmj",
        layer_name: str = "path",
    ):
        if chemin is None:
            chemin = charger_chemin_tiled(tmj_path, layer_name=layer_name)
        if len(chemin) < 2:
            raise ValueError("Chemin invalide (>=2 points requis).")
        self.vitesse = float(vitesse)
        self.pointsDeVie = int(pointsDeVie)
        self.degats = int(degats)
        self._chemin: List[Position] = chemin
        self.position = self._chemin[0].copy()
        self._segment_index = 0
        self._dist_on_segment = 0.0
        self._arrive_au_bout = False
        self.visible = False
        self._on_reach_castle = on_reach_castle
        self.tempsApparition = tempsApparition
        


    @abstractmethod
    def draw(self, ecran: pygame.Surface) -> None:
        """Dessine l’ennemi (implémenté par chaque sous-classe)."""
        raise NotImplementedError

    def apparaitre(self):
        self.position = self._chemin[0].copy()
        self._segment_index = 0
        self._dist_on_segment = 0.0
        self._arrive_au_bout = False
        self.visible = False

    def seDeplacer(self, dt: float):
        if self.estMort() or self._arrive_au_bout:
            return
        d = max(0.0, self.vitesse * dt)
        while d > 1e-6 and not self._arrive_au_bout:
            if self._segment_index >= len(self._chemin) - 1:
                self._arrive()
                break
            p0 = self._chemin[self._segment_index]
            p1 = self._chemin[self._segment_index + 1]
            seg_len = max(1e-9, distance_positions(p0, p1))
            reste = seg_len - self._dist_on_segment
            if d < reste:
                self._dist_on_segment += d
                t = self._dist_on_segment / seg_len
                self.position.x = p0.x + (p1.x - p0.x) * t
                self.position.y = p0.y + (p1.y - p0.y) * t
                d = 0.0
            else:
                self.position.x, self.position.y = p1.x, p1.y
                d -= reste
                self._segment_index += 1
                self._dist_on_segment = 0.0
                if self._segment_index >= len(self._chemin) - 1:
                    self._arrive()
                    break

    def perdreVie(self, degats: int):
        self.pointsDeVie = max(0, self.pointsDeVie - int(degats))

    def getDistance(self, pos: Position) -> float:
        return distance_positions(self.position, pos)

    def set_visibilite(self, visible: bool):
        self.visible = visible

    def estMort(self) -> bool:
        return self.pointsDeVie <= 0

    def a_atteint_le_bout(self) -> bool:
        return self._arrive_au_bout

    def _arrive(self):
        self._arrive_au_bout = True
        if self._on_reach_castle and not self.estMort():
            self._on_reach_castle(self)
    
    def majVisible(self):
        x, y  = pygame.mouse.get_pos()
        pointeurPos = Position(x, y)
        if(distance_positions(self.position, pointeurPos) < 100):
            self.set_visibilite(True)
        else:
            self.set_visibilite(False)

    def estApparu(self, debutVague):
        return self.tempsApparition <= round((pygame.time.get_ticks() - debutVague) / 1000, 1) # conversion en sec


class Gobelin(Ennemi):
    # Attribut de classe partagé par TOUS les gobelins
    _frames: list[pygame.Surface] | None = None  

    @property
    def type_nom(self) -> str: 
        return "Gobelin"

    def __init__(self, tempsApparition: int, chemin: Optional[List[Position]] = None, **kw):
        super().__init__(tempsApparition=tempsApparition, vitesse=80.0, pointsDeVie=60, degats=1, chemin=chemin, **kw)

        # Charger les frames si elles sont vide uniquement la première fois
        if Gobelin._frames is None:
            image = pygame.image.load(os.path.join(base_dir, "assets", "enemy", "goblin", "D_Walk.png")).convert_alpha()
            Gobelin._frames = decouper_sprite(image, nb_images=6, horizontal=True)

        self.frames = Gobelin._frames
        self.frame_index = 0 
        self.frame_timer = 0

    def draw(self, ecran: pygame.Surface) -> None:
        if self.estMort(): 
            return

        # Choisir l’image en fonction de l’animation
        frame = self.frames[self.frame_index]
        pos = (int(self.position.x - frame.get_width() // 2),
               int(self.position.y - frame.get_height() // 2))

        if self.visible:
            ecran.blit(frame, pos)
        else:
            pygame.draw.circle(ecran, (200, 50, 50), (int(self.position.x), int(self.position.y)), 10)

    def update_animation(self, dt: float):
        """Met à jour l’index de frame en fonction du temps (dt = delta time en secondes)."""
        self.frame_timer += dt
        if self.frame_timer >= 0.15:  # change toutes les 150ms
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)


class Rat(Ennemi):
    @property
    def type_nom(self) -> str: return "Rat"
    def __init__(self, tempsApparition: int, chemin: Optional[List[Position]] = None, **kw):
        super().__init__(tempsApparition=tempsApparition, vitesse=120.0, pointsDeVie=30, degats=1, chemin=chemin, **kw)
    def draw(self, ecran: pygame.Surface) -> None:
        if self.estMort(): 
            return
        pos = (int(self.position.x), int(self.position.y))
        if self.visible:
            pygame.draw.circle(ecran, (50, 50, 200), pos, 10)
        else:
            pygame.draw.circle(ecran, (200, 50, 50), pos, 10)

class Loup(Ennemi):
    @property
    def type_nom(self) -> str: return "Loup"
    def __init__(self,tempsApparition: int, chemin: Optional[List[Position]] = None, **kw):
        super().__init__(tempsApparition=tempsApparition, vitesse=100.0, pointsDeVie=90, degats=2, chemin=chemin, **kw)
    def draw(self, ecran: pygame.Surface) -> None:
        if self.estMort(): 
            return
        pos = (int(self.position.x), int(self.position.y))
        if self.visible:
            pygame.draw.circle(ecran, (50, 200, 50), pos, 10)
        else:
            pygame.draw.circle(ecran, (200, 50, 50), pos, 10)

class Mage(Ennemi):
    @property
    def type_nom(self) -> str: return "Mage"
    def __init__(self, tempsApparition: int, chemin: Optional[List[Position]] = None, **kw):
        super().__init__(tempsApparition=tempsApparition, vitesse=70.0, pointsDeVie=120, degats=3, chemin=chemin, **kw)
    def draw(self, ecran: pygame.Surface) -> None:
        if self.estMort(): 
            return
        pos = (int(self.position.x), int(self.position.y))
        if self.visible:
            pygame.draw.circle(ecran, (255, 255, 0), pos, 10)  # jaune
        else:
            pygame.draw.circle(ecran, (200, 50, 50), pos, 10)
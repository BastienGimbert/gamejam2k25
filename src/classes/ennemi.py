from typing import Callable, List, Optional
from abc import ABC, abstractmethod
from classes.position import Position
from classes.utils import charger_chemin_tiled, distance_positions, decouper_sprite
import pygame
import os

SCALE_FACTOR = 2


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

            dx = p1.x - p0.x
            dy = p1.y - p0.y
            if abs(dx) > abs(dy):
                self.direction = "side"
                self.flip = dx > 0   # flip horizontal si on va vers la gauche
            else:
                self.direction = "down" if dy > 0 else "up"
                self.flip = False

            seg_len = max(1e-9, distance_positions(p0, p1))
            reste = seg_len - self._dist_on_segment

            if d < reste:
                self._dist_on_segment += d
                t = self._dist_on_segment / seg_len
                self.position.x = p0.x + (dx * t)
                self.position.y = p0.y + (dy * t)
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
    # Attributs de classe : frames par direction
    _frames_by_dir: dict[str, list[pygame.Surface]] | None = None  

    @property
    def type_nom(self) -> str: 
        return "Gobelin"

    def __init__(self, tempsApparition: int, chemin: Optional[List[Position]] = None, **kw):
        super().__init__(tempsApparition=tempsApparition, vitesse=80.0, pointsDeVie=60, degats=1, chemin=chemin, **kw)

        # Charger les spritesheets une seule fois
        if Gobelin._frames_by_dir is None:
            from classes.utils import decouper_sprite
            Gobelin._frames_by_dir = {
                "down": [pygame.transform.scale(f, (f.get_width()*SCALE_FACTOR, f.get_height()*SCALE_FACTOR)) for f in decouper_sprite(pygame.image.load("assets/enemy/goblin/D_Walk.png").convert_alpha(), 6)],
                "up":   [pygame.transform.scale(f, (f.get_width()*SCALE_FACTOR, f.get_height()*SCALE_FACTOR)) for f in decouper_sprite(pygame.image.load("assets/enemy/goblin/U_Walk.png").convert_alpha(), 6)],
                "side": [pygame.transform.scale(f, (f.get_width()*SCALE_FACTOR, f.get_height()*SCALE_FACTOR)) for f in decouper_sprite(pygame.image.load("assets/enemy/goblin/S_Walk.png").convert_alpha(), 6)],
            }

        self.direction = "down"   # par défaut
        self.frame_index = 0
        self.frame_timer = 0
        self.flip = False

    def update_animation(self, dt: float):
        """Met à jour l’index de frame en fonction du temps (dt)."""
        self.frame_timer += dt
        if self.frame_timer >= 0.15:  # change toutes les 150ms
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(Gobelin._frames_by_dir[self.direction])

    def draw(self, ecran: pygame.Surface) -> None:
        if self.estMort():
            return

        # Récupérer les frames correspondant à la direction
        frames = Gobelin._frames_by_dir[self.direction]
        frame = frames[self.frame_index]

        # Flip horizontal si besoin (uniquement pour "side")
        if self.direction == "side" and self.flip:
            frame = pygame.transform.flip(frame, True, False)

        # Calcul position centrée
        pos = (
            int(self.position.x - frame.get_width() // 2),
            int(self.position.y - frame.get_height() // 2),
        )

        # Dessin
        if self.visible:
            ecran.blit(frame, pos)
        else:
            temp = frame.copy()          # Copier pour ne pas modifier l'original
            temp.set_alpha(90)
            ecran.blit(temp, pos)

SCALE_FACTOR = 2  # redimensionne toutes les frames

class Rat(Ennemi):
    _frames_by_dir: dict[str, list[pygame.Surface]] | None = None

    @property
    def type_nom(self) -> str: return "Rat"

    def __init__(self, tempsApparition: int, chemin: Optional[List[Position]] = None, **kw):
        super().__init__(tempsApparition=tempsApparition, vitesse=120.0, pointsDeVie=30, degats=1, chemin=chemin, **kw)

        if Rat._frames_by_dir is None:
            from classes.utils import decouper_sprite
            def charger_et_scaler(path: str, nb_frames: int):
                frames = decouper_sprite(pygame.image.load(path).convert_alpha(), nb_frames)
                return [pygame.transform.scale(f, (f.get_width()/1.5, f.get_height()/1.5)) for f in frames]

            Rat._frames_by_dir = {
                "down": charger_et_scaler("assets/enemy/rat/D_Run.png", 6),
                "up": charger_et_scaler("assets/enemy/rat/U_Run.png", 6),
                "side": charger_et_scaler("assets/enemy/rat/S_Run.png", 6),
            }

        self.direction = "down"
        self.frame_index = 0
        self.frame_timer = 0
        self.flip = False

    def update_animation(self, dt: float):
        self.frame_timer += dt
        if self.frame_timer >= 0.15:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(Rat._frames_by_dir[self.direction])

    def draw(self, ecran: pygame.Surface) -> None:
        if self.estMort():
            return
        frames = Rat._frames_by_dir[self.direction]
        frame = frames[self.frame_index]
        if self.direction == "side" and self.flip:
            frame = pygame.transform.flip(frame, True, False)
        pos = (int(self.position.x - frame.get_width()//2),
               int(self.position.y - frame.get_height()//2))
        if self.visible:
            ecran.blit(frame, pos)
        else:
            temp = frame.copy()          # Copier pour ne pas modifier l'original
            temp.set_alpha(90)
            ecran.blit(temp, pos)

class Loup(Ennemi):
    _frames_by_dir: dict[str, list[pygame.Surface]] | None = None

    @property
    def type_nom(self) -> str: return "Loup"

    def __init__(self, tempsApparition: int, chemin: Optional[List[Position]] = None, **kw):
        super().__init__(tempsApparition=tempsApparition, vitesse=100.0, pointsDeVie=90, degats=2, chemin=chemin, **kw)

        if Loup._frames_by_dir is None:
            from classes.utils import decouper_sprite
            def charger_et_scaler(path: str, nb_frames: int):
                frames = decouper_sprite(pygame.image.load(path).convert_alpha(), nb_frames)
                return [pygame.transform.scale(f, (f.get_width()*SCALE_FACTOR*1.2, f.get_height()*SCALE_FACTOR*1.2)) for f in frames]

            Loup._frames_by_dir = {
                "down": charger_et_scaler("assets/enemy/wolf/D_Walk.png", 6),
                "up": charger_et_scaler("assets/enemy/wolf/U_Walk.png", 6),
                "side": charger_et_scaler("assets/enemy/wolf/S_Walk.png", 6),
            }

        self.direction = "down"
        self.frame_index = 0
        self.frame_timer = 0
        self.flip = False

    def update_animation(self, dt: float):
        self.frame_timer += dt
        if self.frame_timer >= 0.15:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(Loup._frames_by_dir[self.direction])

    def draw(self, ecran: pygame.Surface) -> None:
        if self.estMort():
            return
        frames = Loup._frames_by_dir[self.direction]
        frame = frames[self.frame_index]
        if self.direction == "side" and self.flip:
            frame = pygame.transform.flip(frame, True, False)
        pos = (int(self.position.x - frame.get_width()//2),
               int(self.position.y - frame.get_height()//2))
        if self.visible:
            ecran.blit(frame, pos)
        else:
            temp = frame.copy()          # Copier pour ne pas modifier l'original
            temp.set_alpha(90)
            ecran.blit(temp, pos)

class Mage(Ennemi):
    _frames_by_dir: dict[str, list[pygame.Surface]] | None = None

    @property
    def type_nom(self) -> str: return "Mage"

    def __init__(self, tempsApparition: int, chemin: Optional[List[Position]] = None, **kw):
        super().__init__(tempsApparition=tempsApparition, vitesse=70.0, pointsDeVie=120, degats=3, chemin=chemin, **kw)

        if Mage._frames_by_dir is None:
            from classes.utils import decouper_sprite
            def charger_et_scaler(path: str, nb_frames: int):
                frames = decouper_sprite(pygame.image.load(path).convert_alpha(), nb_frames)
                return [pygame.transform.scale(f, (f.get_width()*SCALE_FACTOR*0.6, f.get_height()*SCALE_FACTOR*0.6)) for f in frames]

            Mage._frames_by_dir = {
                "down": charger_et_scaler("assets/enemy/mage/D_Fly.png", 6),
                "up": charger_et_scaler("assets/enemy/mage/U_Fly.png", 6),
                "side": charger_et_scaler("assets/enemy/mage/S_Fly.png", 6),
            }

        self.direction = "down"
        self.frame_index = 0
        self.frame_timer = 0
        self.flip = False

    def update_animation(self, dt: float):
        self.frame_timer += dt
        if self.frame_timer >= 0.15:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(Mage._frames_by_dir[self.direction])

    def draw(self, ecran: pygame.Surface) -> None:
        if self.estMort():
            return
        frames = Mage._frames_by_dir[self.direction]
        frame = frames[self.frame_index]
        if self.direction == "side" and self.flip:
            frame = pygame.transform.flip(frame, True, False)
        pos = (int(self.position.x - frame.get_width()//2),
               int(self.position.y - frame.get_height()//2))
        if self.visible:
            ecran.blit(frame, pos)
        else:
            temp = frame.copy()          # Copier pour ne pas modifier l'original
            temp.set_alpha(90)
            ecran.blit(temp, pos)

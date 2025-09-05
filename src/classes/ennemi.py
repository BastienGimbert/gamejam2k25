from typing import Callable, List, Optional
from abc import ABC, abstractmethod
from classes.position import Position
from classes.utils import charger_chemin_tiled, distance_positions, decouper_sprite, charger_et_scaler
import pygame
import os

#Evite les boucles dans les imports mutuels
from typing import TYPE_CHECKING

from classes.constants import TILESETS_DIR, MAP_TILESET_TMJ

if TYPE_CHECKING:
    from game import Game


SCALE_FACTOR = 2


class Ennemi(ABC):
    def __init__(
        self,
        vitesse: float,
        pointsDeVie: int,
        degats: int,
        argent: int,
        tempsApparition = 0,
        chemin: Optional[List[Position]] = None,
        on_reach_castle: Optional[Callable[["Ennemi"], None]] = None,
        tmj_path: str = MAP_TILESET_TMJ,
        layer_name: str = "path",
    ):
        if chemin is None:
            chemin = charger_chemin_tiled(tmj_path, layer_name=layer_name)
        if len(chemin) < 2:
            raise ValueError("Chemin invalide (>=2 points requis).")
        self.vitesse = float(vitesse)
        self.pointsDeVie = int(pointsDeVie)
        self.pointsDeVieMax = int(pointsDeVie)  # PV Max et donc initiaux de l'ennemi
        self.degats = int(degats)
        # Montant d'or donné au joueur quand cet ennemi est tué
        self.argent = int(argent)
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

    def majVisible(self, game: Optional["Game"]):
        x, y = pygame.mouse.get_pos()
        pointeurPos = Position(x, y)
        
        # Vérifier d'abord si l'effet de la fée est actif
        if game and hasattr(game, 'sorts') and 'fee' in game.sorts:
            if game.sorts['fee'].est_actif():
                # Si la fée est active, tous les ennemis sont visibles
                self.set_visibilite(True)
                return
        
        # Portée de base du curseur
        portee_curseur = 100
        
        # Vérifier si le joueur a le sort de vision et augmenter la portée
        if game and hasattr(game, 'sorts') and 'vision' in game.sorts:
            portee_curseur = game.sorts['vision'].portee
        
        if(distance_positions(self.position, pointeurPos) < portee_curseur) or game.dansFeuDeCamp(self.position):
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
        super().__init__(tempsApparition=tempsApparition, vitesse=50.0, pointsDeVie=130, degats=8, argent=3, chemin=chemin, **kw)

        # Charger les spritesheets une seule fois
        if Gobelin._frames_by_dir is None:
            Gobelin._frames_by_dir = {
                "down": charger_et_scaler("goblin", "D_Walk.png", 6, scale=SCALE_FACTOR*0.8),
                "up": charger_et_scaler("goblin", "U_Walk.png", 6, scale=SCALE_FACTOR*0.8),
                "side": charger_et_scaler("goblin", "S_Walk.png", 6, scale=SCALE_FACTOR*0.8),
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
        pos = (int(self.position.x - frame.get_width()//2),
               int(self.position.y - frame.get_height()//2))
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
        super().__init__(tempsApparition=tempsApparition, vitesse=120.0, pointsDeVie=20, degats=3, argent=1, chemin=chemin, **kw)

        if Rat._frames_by_dir is None:
            Rat._frames_by_dir = {
                "down": charger_et_scaler("rat", "D_Run.png", 6, scale=2/3),
                "up": charger_et_scaler("rat", "U_Run.png", 6, scale=2/3),
                "side": charger_et_scaler("rat", "S_Run.png", 6, scale=2/3),
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
        super().__init__(tempsApparition=tempsApparition, vitesse=100.0, pointsDeVie=90, degats=10, argent=2, chemin=chemin, **kw)

        if Loup._frames_by_dir is None:
            Loup._frames_by_dir = {
                "down": charger_et_scaler("wolf", "D_Walk.png", 6, scale=SCALE_FACTOR*0.8),
                "up": charger_et_scaler("wolf", "U_Walk.png", 6, scale=SCALE_FACTOR*0.8),
                "side": charger_et_scaler("wolf", "S_Walk.png", 6, scale=SCALE_FACTOR*0.8),
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

    ATTACK_COOLDOWN = 2.5     # en secondes

    _frames_by_dir: dict[str, list[pygame.Surface]] | None = None

    @property
    def type_nom(self) -> str: return "Mage"

    def __init__(self, tempsApparition: int, chemin: Optional[List[Position]] = None, **kw):
        super().__init__(tempsApparition=tempsApparition, vitesse=50.0, pointsDeVie=180, degats=12, argent=5, chemin=chemin, **kw)

        if Mage._frames_by_dir is None:
            Mage._frames_by_dir = {
                "down": charger_et_scaler("mage", "D_Fly.png", 6, scale=SCALE_FACTOR*0.6),
                "up": charger_et_scaler("mage", "U_Fly.png", 6, scale=SCALE_FACTOR*0.6),
                "side": charger_et_scaler("mage", "S_Fly.png", 6, scale=SCALE_FACTOR*0.6),
            }

        self.direction = "down"
        self.frame_index = 0
        self.frame_timer = 0
        self.flip = False

        self._time_since_last_attack = 10.0


    def update_animation(self, dt: float):
        self.frame_timer += dt
        self._time_since_last_attack += dt

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

    def ready_to_attack(self) -> bool:
        """Retourne True si le cooldown est écoulé et que le mage peut attaquer."""
        return self._time_since_last_attack >= Mage.ATTACK_COOLDOWN

    def react_to_projectile(self):
        """Déclenche l'animation d'attaque du mage."""
        if not self.ready_to_attack():
            return  # ignore si le cooldown n'est pas fini
        print("Mage attaque !")
        # reset du timer
        self._time_since_last_attack = 0.0
        self.frame_index = 0
        self.frame_timer = 0



class Ogre(Ennemi):
    _frames_by_dir: dict[str, list[pygame.Surface]] | None = None

    @property
    def type_nom(self) -> str: return "Ogre"

    def __init__(self, tempsApparition: int, chemin: Optional[List[Position]] = None, **kw):
        super().__init__(tempsApparition=tempsApparition, vitesse=25.0, pointsDeVie=500, degats=30, argent=10, chemin=chemin, **kw)

        if Ogre._frames_by_dir is None:
            Ogre._frames_by_dir = {
                "down": charger_et_scaler("ogre", "D_Walk.png", 6, scale=SCALE_FACTOR),
                "up": charger_et_scaler("ogre", "U_Walk.png", 6, scale=SCALE_FACTOR),
                "side": charger_et_scaler("ogre", "S_Walk.png", 6, scale=SCALE_FACTOR),
            }

        self.direction = "down"
        self.frame_index = 0
        self.frame_timer = 0
        self.flip = False

    def update_animation(self, dt: float):
        self.frame_timer += dt
        if self.frame_timer >= 0.15:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(Ogre._frames_by_dir[self.direction])

    def draw(self, ecran: pygame.Surface) -> None:
        if self.estMort():
            return
        frames = Ogre._frames_by_dir[self.direction]
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
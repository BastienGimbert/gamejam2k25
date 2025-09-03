from typing import Callable, List, Optional
from abc import ABC
from classes.position import Position
from classes.utils import charger_chemin_tiled, distance_positions

class Ennemi(ABC):
    def __init__(
        self,
        id: int,
        vitesse: float,
        pointsDeVie: int,
        degats: int,
        chemin: Optional[List[Position]] = None,
        on_reach_castle: Optional[Callable[["Ennemi"], None]] = None,
        tmj_path: str = "assets/tilesets/carte.tmj",
        layer_name: str = "path",
    ):
        if chemin is None:
            chemin = charger_chemin_tiled(tmj_path, layer_name=layer_name)
        if len(chemin) < 2:
            raise ValueError("Chemin invalide (>=2 points requis).")
        self.id = id
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

    def apparaitre(self):
        self.position = self._chemin[0].copy()
        self._segment_index = 0
        self._dist_on_segment = 0.0
        self._arrive_au_bout = False
        self.visible = True

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

class Gobelin(Ennemi):
    @property
    def type_nom(self) -> str: return "Gobelin"
    def __init__(self, id: int, chemin: Optional[List[Position]] = None, **kw):
        super().__init__(id=id, vitesse=80.0, pointsDeVie=60, degats=1, chemin=chemin, **kw)

class Rat(Ennemi):
    @property
    def type_nom(self) -> str: return "Rat"
    def __init__(self, id: int, chemin: Optional[List[Position]] = None, **kw):
        super().__init__(id=id, vitesse=120.0, pointsDeVie=30, degats=1, chemin=chemin, **kw)

class Loup(Ennemi):
    @property
    def type_nom(self) -> str: return "Loup"
    def __init__(self, id: int, chemin: Optional[List[Position]] = None, **kw):
        super().__init__(id=id, vitesse=100.0, pointsDeVie=90, degats=2, chemin=chemin, **kw)

class Mage(Ennemi):
    @property
    def type_nom(self) -> str: return "Mage"
    def __init__(self, id: int, chemin: Optional[List[Position]] = None, **kw):
        super().__init__(id=id, vitesse=70.0, pointsDeVie=120, degats=3, chemin=chemin, **kw)
from typing import Callable, List, Optional
from abc import ABC

from classes.position import Position
from classes.utils import distance_positions

class Ennemi(ABC):
    """
    Classe de base pour tous les ennemis.
    """

    def __init__(
        # Paramètre de la classe
        self, # sert à initialiser les attributs de l'ennemi
        id: int,
        vitesse: float,               # px/s
        pointsDeVie: int,
        position_depart: Position,    # sera écrasée par apparaître() = chemin[0]
        degats: int,
        chemin: List[Position],
        on_reach_castle: Optional[Callable[["Ennemi"], None]] = None,
    ):
        if not chemin or len(chemin) < 2:
            raise ValueError("Le chemin doit contenir au moins 2 points. Probleme de lecture du TMJ")

        self.id = id
        self.vitesse = float(vitesse)
        self.pointsDeVie = int(pointsDeVie)
        self.position = position_depart.copy()
        self.degats = int(degats)

        self._chemin: List[Position] = chemin
        self._segment_index: int = 0          # segment = [i -> i+1]
        self._dist_on_segment: float = 0.0    # distance parcourue sur le segment courant
        self._arrive_au_bout: bool = False
        self.visible: bool = False

        self._on_reach_castle = on_reach_castle

    def apparaitre(self) -> None:
        """Place l’ennemi sur le premier point du chemin et reset l’état de déplacement."""
        self.position = self._chemin[0].copy()
        self._segment_index = 0
        self._dist_on_segment = 0.0
        self._arrive_au_bout = False

    def seDeplacer(self, dt: float) -> None:
        """Fait avancer l’ennemi de vitesse*dt le long du chemin. dt en secondes."""
        if self.estMort() or self._arrive_au_bout:
            return

        distance_a_parcourir = max(0.0, float(self.vitesse) * float(dt))

        while distance_a_parcourir > 1e-6 and not self._arrive_au_bout:
            if self._segment_index >= len(self._chemin) - 1:
                # déjà au bout
                self._arrive()
                break

            p0 = self._chemin[self._segment_index]
            p1 = self._chemin[self._segment_index + 1]
            seg_len = max(1e-9, distance_positions(p0, p1))  # évite division par 0
            reste_seg = seg_len - self._dist_on_segment

            if distance_a_parcourir < reste_seg:
                # Avance à l’intérieur du segment
                self._dist_on_segment += distance_a_parcourir
                t = self._dist_on_segment / seg_len
                self.position.x = p0.x + (p1.x - p0.x) * t
                self.position.y = p0.y + (p1.y - p0.y) * t
                distance_a_parcourir = 0.0
            else:
                # Fin de segment -> se placer pile au point p1, puis passer au segment suivant
                self.position.x, self.position.y = p1.x, p1.y
                distance_a_parcourir -= reste_seg
                self._segment_index += 1
                self._dist_on_segment = 0.0

                if self._segment_index >= len(self._chemin) - 1:
                    self._arrive()
                    break

    def perdreVie(self, degats: int) -> None:
        """Inflige des dégâts et gèle le déplacement s’il meurt."""
        self.pointsDeVie = max(0, self.pointsDeVie - int(degats))

    def getDistance(self, pos: Position) -> float:
        """Distance entre cet ennemi et une position."""
        return distance_positions(self.position, pos)

    def set_visibilite(self, visible: bool) -> None:
        """Définit directement la visibilité de l'ennemi."""
        self.visible = visible

    # ---- État ----
    def estMort(self) -> bool:
        return self.pointsDeVie <= 0

    def a_atteint_le_bout(self) -> bool:
        return self._arrive_au_bout

    def _arrive(self) -> None:
        self._arrive_au_bout = True
        if self._on_reach_castle and not self.estMort():
            self._on_reach_castle(self)


class Gobelin(Ennemi):
    def __init__(
        self, id: int, chemin: List[Position], on_reach_castle: Optional[Callable[["Ennemi"], None]] = None
    ):
        super().__init__(id=id, vitesse=80.0, pointsDeVie=60, position_depart=chemin[0], degats=1, chemin=chemin, on_reach_castle=on_reach_castle)
    @property
    def type_nom(self) -> str: return "Gobelin"

class Rat(Ennemi):
    def __init__(
        self, id: int, chemin: List[Position], on_reach_castle: Optional[Callable[["Ennemi"], None]] = None
    ):
        super().__init__(id=id, vitesse=120.0, pointsDeVie=30, position_depart=chemin[0], degats=1, chemin=chemin, on_reach_castle=on_reach_castle)
    @property
    def type_nom(self) -> str: return "Rat"

class Loup(Ennemi):
    def __init__(
        self, id: int, chemin: List[Position], on_reach_castle: Optional[Callable[["Ennemi"], None]] = None
    ):
        super().__init__(id=id, vitesse=100.0, pointsDeVie=90, position_depart=chemin[0], degats=2, chemin=chemin, on_reach_castle=on_reach_castle)
    @property
    def type_nom(self) -> str: return "Loup"

class Mage(Ennemi):
    def __init__(
        self, id: int, chemin: List[Position], on_reach_castle: Optional[Callable[["Ennemi"], None]] = None
    ):
        super().__init__(id=id, vitesse=70.0, pointsDeVie=120, position_depart=chemin[0], degats=3, chemin=chemin, on_reach_castle=on_reach_castle)
    @property
    def type_nom(self) -> str: return "Mage"

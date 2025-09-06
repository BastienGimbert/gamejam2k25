import os
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Tuple

import pygame

from classes.animation import DirectionalAnimator
from classes.ennemi import Ennemi
from classes.position import Position
from classes.utils import charger_et_scaler, distance_positions


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


class Tour(ABC):
    def __init__(
        self,
        id: int,
        type_id: int,
        type_nom: str,
        cooldown_s: float,
        portee: float,
        position: Position,
        prix: int = 0,
    ) -> None:
        self.id = int(id)
        self.type_id = int(type_id)
        self.type_nom = str(type_nom)
        self.cooldown_s = float(cooldown_s)
        self.portee = float(portee)
        self.position = position
        self._time_since_last_shot = 0.0

        # Caractéristiques de gameplay (les dégâts sont portés par les projectiles)
        self.prix = int(prix)

        self._etat = "idle"
        self._cible: Optional["Ennemi"] = None
        self._au_tir: Optional[Callable[["Tour", "Ennemi"], None]] = None

        person_path = os.path.join(
            _project_root(), "assets", "tower", self.type_nom, "person"
        )
        desired_total = 6 if self.type_nom == "catapulte" else 11
        side_faces_right = False if self.type_nom == "archer" else True
        self._anim = DirectionalAnimator(
            person_path,
            side_faces_right=side_faces_right,
            desired_compound_total=desired_total,
        )
        self._anim.start("Idle", "S", False)

        offsets = {"archer": -18, "catapulte": 2, "mage": -18}
        self._person_offset_y = offsets.get(self.type_nom, 8)

    def draw(self, ecran: pygame.Surface) -> None:
        rect = pygame.Rect(int(self.position.x) - 16, int(self.position.y) - 16, 32, 32)
        pygame.draw.rect(ecran, (150, 150, 180), rect)
        self.draw_person(ecran)

    def draw_person(self, ecran: pygame.Surface) -> None:
        self._anim.draw(
            ecran,
            int(self.position.x),
            int(self.position.y) - self._person_offset_y,
        )

    def maj(
        self,
        dt: float,
        ennemis: List["Ennemi"],
        au_tir: Optional[Callable[["Tour", "Ennemi"], None]] = None,
    ) -> None:
        if dt < 0:
            return

        if self._etat == "idle":
            self._time_since_last_shot += dt
            self._anim.update(dt)
            if self._time_since_last_shot >= self.cooldown_s:
                cible = self._choisir_cible(ennemis)
                if cible is not None:
                    self._cible = cible
                    d, fx = self._best_orient(self._cible)
                    self._anim.start("Preattack", d, fx)
                    self._etat = "preattack"
                    self._au_tir = au_tir

        elif self._etat == "preattack":
            if self._cible is not None:
                d, fx = self._best_orient(self._cible)
                self._anim.set_orientation(d, fx)
            if self._anim.update(dt):
                d = self._anim.direction
                fx = self._anim.flip_x
                self._anim.start("Attack", d, fx)
                self._etat = "attack"
                if self._cible is not None:
                    self.attaquer(self._cible)

        elif self._etat == "attack":
            if self._cible is not None:
                d, fx = self._best_orient(self._cible)
                self._anim.set_orientation(d, fx)
            if self._anim.update(dt):
                if (
                    self._cible is not None
                    and not self._cible.estMort()
                    and self._cible.visible
                ):
                    if (
                        distance_positions(self.position, self._cible.position)
                        <= self.portee
                    ):
                        if self._au_tir is not None:
                            self._au_tir(self, self._cible)
                            self._time_since_last_shot = 0.0

                self._etat = "idle"
                self._cible = None
                self._au_tir = None
                self._anim.start("Idle", self._anim.direction, self._anim.flip_x)

    def _best_orient(self, cible: Optional["Ennemi"]) -> Tuple[str, bool]:
        if cible is None:
            return "S", False
        return self._anim.best_orientation(
            self.position.x, self.position.y, cible.position.x, cible.position.y
        )

    def _choisir_cible(self, ennemis: List["Ennemi"]) -> Optional["Ennemi"]:
        candidats: List[tuple[float, Ennemi]] = []
        for e in ennemis:
            if e.estMort() or not e.visible:
                continue
            if distance_positions(self.position, e.position) <= self.portee:
                try:
                    fin = e._chemin[-1]
                except Exception:
                    fin = e.position
                d_end = distance_positions(e.position, fin)
                candidats.append((d_end, e))
        if not candidats:
            return None
        candidats.sort(key=lambda t: t[0])
        return candidats[0][1]

    @abstractmethod
    def attaquer(self, cible: "Ennemi") -> None:
        return


class Archer(Tour):
    TYPE_ID = 1
    TYPE_NOM = "archer"
    PORTEE = 150.0

    # Prix indicatif de la tour Archer (affiché dans la boutique)
    PRIX = 20

    def __init__(self, id: int, position: Position) -> None:
        super().__init__(
            id=id,
            type_id=self.TYPE_ID,
            type_nom=self.TYPE_NOM,
            cooldown_s=0.5,
            portee=self.PORTEE,
            position=position,
            prix=self.PRIX,
        )

    def attaquer(self, cible: "Ennemi") -> None:
        return


class Catapulte(Tour):
    TYPE_ID = 2
    TYPE_NOM = "catapulte"
    PORTEE = 220.0

    # Prix indicatif de la tour Catapulte (affiché dans la boutique)
    PRIX = 50

    def __init__(self, id: int, position: Position) -> None:
        super().__init__(
            id=id,
            type_id=self.TYPE_ID,
            type_nom=self.TYPE_NOM,
            cooldown_s=2.0,
            portee=self.PORTEE,
            position=position,
            prix=self.PRIX,
        )

    def attaquer(self, cible: "Ennemi") -> None:
        return


class Mage(Tour):
    TYPE_ID = 3
    TYPE_NOM = "mage"
    PORTEE = 150.0

    # Prix indicatif de la tour Catapulte (affiché dans la boutique)
    PRIX = 60

    def __init__(self, id: int, position: Position) -> None:
        super().__init__(
            id=id,
            type_id=self.TYPE_ID,
            type_nom=self.TYPE_NOM,
            cooldown_s=1.5,
            portee=self.PORTEE,
            position=position,
            prix=self.PRIX,
        )

    def attaquer(self, cible: "Ennemi") -> None:
        return


class Campement(Tour):
    TYPE_ID = 4
    TYPE_NOM = "Campement"
    PRIX = 60
    PORTEE = 92.0

    _frames: list[pygame.Surface] | None = None

    def __init__(self, id: int, position: Position) -> None:
        super().__init__(
            id=id,
            type_id=self.TYPE_ID,
            type_nom=self.TYPE_NOM,
            cooldown_s=1.5,
            portee=self.PORTEE,
            position=position,
            prix=self.PRIX,
        )

        if Campement._frames is None:
            # Charger les 6 frames de feu
            Campement._frames = charger_et_scaler(
                "tower/campement", "1.png", 6, scale=0.8, notInEnemyFolder=True
            )

        self.frame_index = 0
        self.frame_timer = 0.0

    def maj(self, dt: float, *args, **kwargs) -> None:
        self.frame_timer += dt
        if self.frame_timer >= 0.12:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(Campement._frames)

    def dessiner(self, ecran: pygame.Surface, taille_case: int) -> None:
        if Campement._frames is None:
            return
        frame = Campement._frames[self.frame_index]
        surf = pygame.transform.smoothscale(frame, (taille_case, taille_case))
        offset_y = -15 # Ajustement vertical pour centrer le feu
        ecran.blit(
            surf,
            (self.position.x - taille_case // 2, self.position.y - taille_case // 2 + offset_y),
        )

    def attaquer(self, cible: "Ennemi") -> None:
        pass

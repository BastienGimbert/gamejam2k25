import os
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Tuple

import pygame

from classes.animation import AnimateurDirectionnel
from classes.position import Position
from classes.sprites import charger_sprites_tour
from classes.utils import distance_positions
from models.ennemi import Ennemi


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
        self._anim = AnimateurDirectionnel(
            person_path,
            cote_face_droite=side_faces_right,
            total_frames_desire=desired_total,
        )
        self._anim.demarrer("Idle", "S", False)

        offsets = {"archer": -18, "catapulte": 2, "mage": -18}
        self._person_offset_y = offsets.get(self.type_nom, 8)

    def draw(self, ecran: pygame.Surface) -> None:
        rect = pygame.Rect(int(self.position.x) - 16, int(self.position.y) - 16, 32, 32)
        pygame.draw.rect(ecran, (150, 150, 180), rect)
        self.draw_person(ecran)

    def draw_person(self, ecran: pygame.Surface) -> None:
        self._anim.dessiner(
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
            self._anim.mettre_a_jour(dt)
            if self._time_since_last_shot >= self.cooldown_s:
                cible = self._choisir_cible(ennemis)
                if cible is not None:
                    self._cible = cible
                    d, fx = self._best_orient(self._cible)
                    self._anim.demarrer("Preattack", d, fx)
                    self._etat = "preattack"
                    self._au_tir = au_tir

        elif self._etat == "preattack":
            if self._cible is not None:
                d, fx = self._best_orient(self._cible)
                self._anim.definir_orientation(d, fx)
            if self._anim.mettre_a_jour(dt):
                d = self._anim.direction
                fx = self._anim.flip_x
                self._anim.demarrer("Attack", d, fx)
                self._etat = "attack"
                if self._cible is not None:
                    self.attaquer(self._cible)

        elif self._etat == "attack":
            if self._cible is not None:
                d, fx = self._best_orient(self._cible)
                self._anim.definir_orientation(d, fx)
            if self._anim.mettre_a_jour(dt):
                if self._cible is not None and not self._cible.estMort():
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
                self._anim.demarrer("Idle", self._anim.direction, self._anim.flip_x)

    def _best_orient(self, cible: Optional["Ennemi"]) -> Tuple[str, bool]:
        if cible is None:
            return "S", False
        return self._anim.meilleure_orientation(
            self.position.x, self.position.y, cible.position.x, cible.position.y
        )

    def _choisir_cible(self, ennemis: List["Ennemi"]) -> Optional["Ennemi"]:
        """
        Choisit la cible parmi les ennemis dans la portée de la tour.
        
        Stratégie de ciblage : Priorité aux ennemis les plus proches de l'arrivée.
        Cette stratégie maximise l'efficacité en éliminant d'abord les ennemis
        qui représentent le plus grand danger immédiat.
        
        Args:
            ennemis: Liste de tous les ennemis du jeu
            
        Returns:
            L'ennemi ciblé ou None si aucun ennemi valide dans la portée
        """
        candidats: List[tuple[float, Ennemi]] = []
        
        # 1. Filtrer les ennemis valides dans la portée
        for ennemi in ennemis:
            # Ignorer les ennemis morts ou invisibles
            if ennemi.estMort() or not ennemi.visible:
                continue
                
            # Vérifier si l'ennemi est dans la portée de la tour
            distance_tour_ennemi = distance_positions(self.position, ennemi.position)
            if distance_tour_ennemi <= self.portee:
                # Calculer la distance restante jusqu'à l'arrivée
                distance_restante = ennemi.get_distance_restante()
                candidats.append((distance_restante, ennemi))

        # 2. Aucun ennemi valide trouvé
        if not candidats:
            return None

        # 3. Trouver l'ennemi avec la plus petite distance restante
        # (le plus proche de l'arrivée = le plus dangereux)
        meilleur_candidat = candidats[0]
        for candidat in candidats[1:]:
            if candidat[0] < meilleur_candidat[0]:
                meilleur_candidat = candidat

        return meilleur_candidat[1]

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
    PORTEE = 230.0

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

    def _choisir_cible(self, ennemis: List["Ennemi"]) -> Optional["Ennemi"]:
        """
        Choisit la cible parmi les ennemis dans la portée de la catapulte.
        
        Stratégie de ciblage spéciale pour la catapulte : Priorité aux ennemis
        avec le plus de points de vie (boss/ennemis forts). En cas d'égalité de PV,
        on privilégie celui le plus proche de l'arrivée.
        
        Cette stratégie est logique car la catapulte a un cooldown élevé et des
        dégâts élevés, donc elle doit cibler les ennemis les plus résistants.
        
        Args:
            ennemis: Liste de tous les ennemis du jeu
            
        Returns:
            L'ennemi ciblé ou None si aucun ennemi valide dans la portée
        """
        candidats: List[tuple[int, float, Ennemi]] = []
        
        # 1. Filtrer les ennemis valides dans la portée
        for ennemi in ennemis:
            # Ignorer les ennemis morts ou invisibles
            if ennemi.estMort() or not ennemi.visible:
                continue
                
            # Vérifier si l'ennemi est dans la portée de la catapulte
            distance_tour_ennemi = distance_positions(self.position, ennemi.position)
            if distance_tour_ennemi <= self.portee:
                # Stocker (PV_initiaux, distance_restante, ennemi) pour le tri
                candidats.append((
                    ennemi.pointsDeVieInitiaux,  # PV initiaux (critère principal)
                    ennemi.get_distance_restante(),  # Distance restante (critère secondaire)
                    ennemi
                ))

        # 2. Aucun ennemi valide trouvé
        if not candidats:
            return None

        # 3. Trouver l'ennemi avec le plus de PV (boss/ennemis forts)
        meilleur_candidat = candidats[0]
        for candidat in candidats[1:]:
            pv_candidat = candidat[0]
            pv_meilleur = meilleur_candidat[0]
            
            if pv_candidat > pv_meilleur:
                # Candidat a plus de PV → nouveau meilleur
                meilleur_candidat = candidat
            elif pv_candidat == pv_meilleur:
                # Égalité de PV → privilégier celui le plus proche de l'arrivée
                distance_candidat = candidat[1]
                distance_meilleur = meilleur_candidat[1]
                if distance_candidat < distance_meilleur:
                    meilleur_candidat = candidat

        return meilleur_candidat[2]  # Retourner l'ennemi (3ème élément du tuple)


class Mage(Tour):
    TYPE_ID = 3
    TYPE_NOM = "mage"
    PORTEE = 190.0

    # Prix indicatif de la tour Mage (affiché dans la boutique)
    PRIX = 100

    def __init__(self, id: int, position: Position) -> None:
        super().__init__(
            id=id,
            type_id=self.TYPE_ID,
            type_nom=self.TYPE_NOM,
            cooldown_s=0.4,
            portee=self.PORTEE,
            position=position,
            prix=self.PRIX,
        )

    def attaquer(self, cible: "Ennemi") -> None:
        return

    def maj(
        self,
        dt: float,
        ennemis: List["Ennemi"],
        au_tir: Optional[Callable[["Tour", "Ennemi"], None]] = None,
    ) -> None:
        if dt < 0:
            return

        self._time_since_last_shot += dt
        self._anim.mettre_a_jour(dt)

        if self._time_since_last_shot >= self.cooldown_s:
            cible = self._choisir_cible(ennemis)
            if cible is not None and au_tir is not None:
                au_tir(self, cible)
                self._time_since_last_shot = 0.0


class Campement(Tour):
    TYPE_ID = 4
    TYPE_NOM = "Campement"
    PRIX = 60
    PORTEE = 100.0

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
            Campement._frames = charger_sprites_tour("campement", "1.png", 6, scale=0.8)

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
        offset_y = -15  # Ajustement vertical pour centrer le feu
        ecran.blit(
            surf,
            (
                self.position.x - taille_case // 2,
                self.position.y - taille_case // 2 + offset_y,
            ),
        )

    def attaquer(self, cible: "Ennemi") -> None:
        pass

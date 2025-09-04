from abc import ABC, abstractmethod
from typing import List, Optional, Callable

import pygame

from classes.position import Position
from classes.utils import distance_positions
from classes.ennemi import Ennemi
from classes.projectile import ProjectileFleche


class Tour(ABC):
    """Base générique d'une tour.

    Inspirée de la structure de `Ennemi`: on regroupe les données et le
    comportement de la tour. La mise à jour se fait à chaque tick via la
    méthode `maj`, à laquelle on passe le `dt` (delta temps) et la liste
    d'ennemis visibles.
    """

    def __init__(
        self,
        id: int,
        type_id: int,
        type_nom: str,
        cooldown_s: float,
        portee: float,
        position: Position,
    ) -> None:
        # Identifiants et métadonnées
        self.id = int(id)  # Identifiant unique de l'instance de tour
        self.type_id = int(type_id)  # Identifiant du type (1=Archer, 2=Catapult, ...)
        self.type_nom = str(type_nom)  # Nom lisible du type

        # Caractéristiques de gameplay (les dégâts sont portés par les projectiles)
        self.cooldown_s = float(cooldown_s)  # Temps entre deux tirs (en secondes)
        self.portee = float(portee)  # Portée de tir en pixels
        self.position = position  # Centre de la tour (pixels)

        # Etat interne: accumulateur de temps depuis le dernier tir
        self._time_since_last_shot = 0.0

    # --- Interface d'affichage ---
    def draw(self, ecran: pygame.Surface) -> None:
        """Affichage minimaliste par défaut (surcharge optionnelle).

        Le jeu peut aussi dessiner via ses assets. Cette méthode sert de
        fallback pour du debug.
        """
        rect = pygame.Rect(int(self.position.x) - 16, int(self.position.y) - 16, 32, 32)
        pygame.draw.rect(ecran, (150, 150, 180), rect)

    # --- Boucle de mise à jour ---
    def maj(self, dt: float, ennemis: List[Ennemi], au_tir: Optional[Callable[["Tour", Ennemi], None]] = None) -> None:
        if dt < 0:
            return
        # Accumule le temps pour gérer le cooldown
        self._time_since_last_shot += dt
        if self._time_since_last_shot < self.cooldown_s:
            return

        # Sélectionne une cible dans la portée
        cible = self._choisir_cible(ennemis)
        if cible is None:
            return

        # Hook optionnel
        self.attaquer(cible)
        # Déclenche la création du projectile
        if au_tir is not None:
            au_tir(self, cible)
        self._time_since_last_shot = 0.0

    def _choisir_cible(self, ennemis: List[Ennemi]) -> Optional[Ennemi]:
        # Cible: ennemi dans la portée le plus proche du château (fin du chemin)
        candidats: List[tuple[float, Ennemi]] = []
        for e in ennemis:
            if e.estMort():
                continue
            # Dans la portée par rapport à la tour
            if distance_positions(self.position, e.position) <= self.portee:
                try:
                    fin = e._chemin[-1]  # accès interne assumé
                except Exception:
                    fin = e.position  # fallback
                d_end = distance_positions(e.position, fin)
                candidats.append((d_end, e))
        if not candidats:
            return None
        candidats.sort(key=lambda t: t[0])
        return candidats[0][1]

    @abstractmethod
    def attaquer(self, cible: Ennemi) -> None:
        """Point d'extension éventuel (effets, debuffs). Les dégâts viennent des projectiles."""
        return


class Archer(Tour):
    """Tour rapide à faibles dégâts.

    Equilibrage de base: petits dégâts mais faible cooldown.
    Utiliser pour nettoyer les petits ennemis ou finir les cibles.
    """

    TYPE_ID = 1
    TYPE_NOM = "archer"

    def __init__(self, id: int, position: Position) -> None:
        # Dégâts et cadence de tir équilibrés pour un début
        super().__init__(
            id=id,
            type_id=self.TYPE_ID,
            type_nom=self.TYPE_NOM,
            cooldown_s=0.5,  # tire 2 fois par seconde
            portee=160.0,
            position=position,
        )

    def attaquer(self, cible: Ennemi) -> None:
        return


class Catapult(Tour):
    """Tour lente à gros dégâts.

    Equilibrage de base: gros dégâts mais cooldown élevé.
    Utile contre les ennemis plus résistants. Un effet de zone (splash)
    pourra être ajouté ultérieurement.
    """

    TYPE_ID = 2
    TYPE_NOM = "catapult"

    def __init__(self, id: int, position: Position) -> None:
        super().__init__(
            id=id,
            type_id=self.TYPE_ID,
            type_nom=self.TYPE_NOM,
            cooldown_s=2.0,  # tire toutes les 2 secondes
            portee=200.0,
            position=position,
        )

    def attaquer(self, cible: Ennemi) -> None:
        return

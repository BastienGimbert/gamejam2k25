import os
from typing import Dict, List, Optional, Tuple

import pygame

from classes.sprites import charger_image_simple, decouper_sprite


def _obtenir_racine_projet() -> str:
    """Retourne le chemin racine du projet."""
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def _extraire_direction_du_nom_fichier(nom_fichier: str) -> Optional[str]:
    """
    Extrait la direction depuis le nom d'un fichier d'animation.

    Args:
        nom_fichier: Nom du fichier (ex: "D_Idle.png", "S_Attack.png")

    Returns:
        Direction extraite ("D", "S", "U", "DS", "US") ou None si invalide
    """
    nom_base = os.path.splitext(os.path.basename(nom_fichier))[0]
    token = nom_base.split("_", 1)[0].upper()
    if token in {"D", "S", "U", "DS", "US"}:
        return token
    return None


class AnimateurDirectionnel:
    """
    Gestionnaire d'animations directionnelles pour les personnages.

    Cette classe gère les animations de personnages avec différentes directions
    (haut, bas, côtés, diagonales) et différents états (repos, pré-attaque, attaque).
    """

    def __init__(
        self,
        chemin_personnage_base: str,
        frames_par_etat: Optional[Dict[str, int]] = None,
        durees: Optional[Dict[str, float]] = None,
        etats_en_boucle: Tuple[str, ...] = ("Idle",),
        cote_face_droite: bool = True,
        total_frames_desire: Optional[int] = None,
    ) -> None:
        """
        Initialise l'animateur directionnel.

        Args:
            chemin_personnage_base: Chemin vers le dossier contenant les sprites du personnage
            frames_par_etat: Nombre de frames pour chaque état (défaut: Repos=4, PreAttaque=1, Attaque=6)
            durees: Durée d'affichage de chaque frame par état en secondes
            etats_en_boucle: États qui se répètent en boucle (défaut: Repos)
            cote_face_droite: Si True, le côté "S" regarde vers la droite
            total_frames_desire: Nombre total de frames souhaité pour les sprites composés
        """
        # Configuration du chemin
        self.chemin_personnage_base = (
            chemin_personnage_base
            if os.path.isabs(chemin_personnage_base)
            else os.path.join(_obtenir_racine_projet(), chemin_personnage_base)
        )

        # Configuration des états d'animation
        self.frames_par_etat = frames_par_etat or {
            "Idle": 4,
            "Preattack": 1,
            "Attack": 6,
        }
        self.ordre_etats: List[str] = ["Idle", "Preattack", "Attack"]
        self.durees = durees or {"Idle": 0.18, "Preattack": 0.10, "Attack": 0.10}
        self.etats_en_boucle = set(etats_en_boucle)
        self.cote_face_droite = cote_face_droite
        self.total_frames_desire = total_frames_desire

        # Découverte des directions disponibles
        self.directions: Tuple[str, ...] = self._decouvrir_directions()
        if not self.directions:
            self.directions = ("D", "S", "U")  # Directions par défaut

        # Stockage des frames chargées
        self.frames: Dict[Tuple[str, str], List[pygame.Surface]] = {}
        self._a_sprite_par_etat: Dict[str, bool] = {}

        # État actuel de l'animation
        self.etat = "Idle"
        self.direction = "S"
        self.flip_x = False
        self.index = 0
        self.timer = 0.0

        # Chargement de toutes les animations
        self._charger_toutes_animations()

    def _decouvrir_directions(self) -> Tuple[str, ...]:
        """
        Découvre automatiquement les directions disponibles dans le dossier.

        Returns:
            Tuple des directions trouvées, triées par priorité
        """
        directions = []
        if os.path.isdir(self.chemin_personnage_base):
            for nom_fichier in os.listdir(self.chemin_personnage_base):
                if not nom_fichier.lower().endswith(".png"):
                    continue
                direction = _extraire_direction_du_nom_fichier(nom_fichier)
                if direction and direction not in directions:
                    directions.append(direction)

        # Tri par priorité : diagonales d'abord, puis directions principales
        priorite = ["D", "S", "U", "DS", "US"]
        directions.sort(key=lambda d: priorite.index(d) if d in priorite else 99)
        return tuple(directions)

    def _charger_image(self, chemin: str) -> Optional[pygame.Surface]:
        """
        Charge une image avec gestion d'erreur.

        Args:
            chemin: Chemin vers l'image à charger

        Returns:
            Surface pygame ou None si erreur
        """
        return charger_image_simple(chemin, convert_alpha=True)

    def _calculer_nombre_frames_divisible(
        self, largeur: int, nombre_prefere: int
    ) -> int:
        """
        Calcule le nombre de frames qui divise parfaitement la largeur de l'image.

        Args:
            largeur: Largeur de l'image en pixels
            nombre_prefere: Nombre de frames préféré

        Returns:
            Nombre de frames optimal pour la découpe
        """
        if nombre_prefere and nombre_prefere >= 2 and largeur % nombre_prefere == 0:
            return nombre_prefere

        # Recherche dans des valeurs communes
        for n in (6, 8, 10, 12, 4, 5, 7, 9):
            if largeur % n == 0:
                return n

        # Recherche exhaustive si nécessaire
        for n in range(2, 41):
            if largeur % n == 0:
                return n

        return 1

    def _charger_pour_direction(
        self, direction: str
    ) -> Dict[str, List[pygame.Surface]]:
        """
        Charge toutes les animations pour une direction donnée.

        Args:
            direction: Direction à charger ("D", "S", "U", "DS", "US")

        Returns:
            Dictionnaire {état: [frames]} pour cette direction
        """
        resultat: Dict[str, List[pygame.Surface]] = {}
        a_sprite_par_etat = False

        # Vérifier s'il y a des fichiers séparés par état
        for etat in self.ordre_etats:
            chemin_etat = os.path.join(
                self.chemin_personnage_base, f"{direction}_{etat}.png"
            )
            if os.path.exists(chemin_etat):
                a_sprite_par_etat = True
                break

        self._a_sprite_par_etat[direction] = a_sprite_par_etat

        if a_sprite_par_etat:
            # Chargement des fichiers séparés par état
            for etat in self.ordre_etats:
                chemin_etat = os.path.join(
                    self.chemin_personnage_base, f"{direction}_{etat}.png"
                )
                sprite = self._charger_image(chemin_etat)

                if sprite is None:
                    # Surface transparente de fallback
                    surface_fallback = pygame.Surface((1, 1), pygame.SRCALPHA)
                    surface_fallback.fill((0, 0, 0, 0))
                    resultat[etat] = [surface_fallback]
                else:
                    # Découpage selon le nombre de frames configuré
                    nb_frames = self.frames_par_etat.get(etat, 1)
                    resultat[etat] = decouper_sprite(
                        sprite, nb_frames, horizontal=True, copy=True
                    )

            return resultat

        # Chargement d'un fichier composé unique
        chemin_unique = os.path.join(self.chemin_personnage_base, f"{direction}.png")
        sprite = self._charger_image(chemin_unique)

        if sprite is None:
            # Surface transparente de fallback
            surface_fallback = pygame.Surface((1, 1), pygame.SRCALPHA)
            surface_fallback.fill((0, 0, 0, 0))
            return {
                "Idle": [surface_fallback],
                "Preattack": [surface_fallback],
                "Attack": [surface_fallback],
            }

        # Calcul du nombre optimal de frames
        largeur = sprite.get_width()
        target_n = self.total_frames_desire or 6
        nb_frames = self._calculer_nombre_frames_divisible(largeur, target_n)
        frames = decouper_sprite(sprite, nb_frames, horizontal=True, copy=True)

        # Répartition des frames selon les états
        if nb_frames >= 6:
            # Assez de frames pour une répartition complète
            repos = [frames[0]]
            pre_attaque = [frames[0]]
            attaque = frames
        else:
            # Répartition minimale
            repos = [frames[0]]
            pre_attaque = [frames[0]]
            attaque = frames

        resultat["Idle"] = repos
        resultat["Preattack"] = pre_attaque
        resultat["Attack"] = attaque
        return resultat

    def _charger_toutes_animations(self) -> None:
        """Charge toutes les animations pour toutes les directions."""
        for direction in self.directions:
            animations = self._charger_pour_direction(direction)
            for etat in self.ordre_etats:
                self.frames[(direction, etat)] = animations.get(
                    etat, animations.get("Idle", [])
                )

    def demarrer(
        self, etat: str, direction: Optional[str] = None, flip_x: Optional[bool] = None
    ) -> None:
        """
        Démarre une nouvelle animation.

        Args:
            etat: État à jouer ("Idle", "Preattack", "Attack")
            direction: Direction à utiliser (optionnel)
            flip_x: Inversion horizontale (optionnel)
        """
        if direction is not None:
            self.direction = direction
        if flip_x is not None:
            # L'inversion n'est appliquée que pour les directions latérales
            self.flip_x = flip_x if self.direction in ("S", "DS", "US") else False
        self.etat = etat
        self.index = 0
        self.timer = 0.0

    def definir_orientation(self, direction: str, flip_x: bool) -> None:
        """
        Définit l'orientation du personnage.

        Args:
            direction: Direction ("D", "S", "U", "DS", "US")
            flip_x: Inversion horizontale
        """
        self.direction = direction
        self.flip_x = flip_x if direction in ("S", "DS", "US") else False

    def mettre_a_jour(self, dt: float) -> bool:
        """
        Met à jour l'animation.

        Args:
            dt: Temps écoulé depuis la dernière mise à jour en secondes

        Returns:
            True si l'animation est terminée, False sinon
        """
        frames = self.frames.get((self.direction, self.etat), [])
        if not frames:
            return False

        self.timer += max(0.0, dt)
        termine = False
        duree_frame = self.durees.get(self.etat, 0.1)

        # Avancement des frames
        while self.timer >= duree_frame:
            self.timer -= duree_frame
            self.index += 1

            if self.index >= len(frames):
                if self.etat in self.etats_en_boucle:
                    # Boucle sur la première frame
                    self.index = 0
                else:
                    # Reste sur la dernière frame
                    self.index = len(frames) - 1
                    termine = True
                    break

        return termine

    def dessiner(self, surface: pygame.Surface, centre_x: int, base_y: int) -> None:
        """
        Dessine l'animation sur la surface.

        Args:
            surface: Surface de destination
            centre_x: Position X du centre du personnage
            base_y: Position Y de la base du personnage
        """
        frames = self.frames.get((self.direction, self.etat), [])
        if not frames:
            return

        image = frames[self.index]

        # Application de l'inversion horizontale si nécessaire
        if self.flip_x:
            image = pygame.transform.flip(image, True, False)

        # Positionnement centré en bas
        rect = image.get_rect()
        rect.midbottom = (centre_x, base_y)
        surface.blit(image, rect)

    def meilleure_orientation(
        self, src_x: float, src_y: float, dst_x: float, dst_y: float
    ) -> Tuple[str, bool]:
        """
        Calcule la meilleure orientation pour regarder vers une cible.

        Args:
            src_x, src_y: Position de la source
            dst_x, dst_y: Position de la cible

        Returns:
            Tuple (direction, flip_x) optimal
        """
        dx = float(dst_x - src_x)
        dy = float(dst_y - src_y)
        ax, ay = abs(dx), abs(dy)

        # Vérification de la disponibilité des directions diagonales
        a_diagonales = ("DS" in self.directions) or ("US" in self.directions)

        # Utilisation des diagonales si le ratio est approprié
        if a_diagonales and min(ax, ay) > 0 and max(ax, ay) / min(ax, ay) <= 1.75:
            direction = "DS" if dy >= 0 else "US"
            flip = dx < 0 if self.cote_face_droite else dx > 0

            # Fallback si la direction diagonale n'est pas disponible
            if direction not in self.directions:
                return ("D" if dy > 0 else "U"), flip

            return direction, flip

        # Direction latérale si le mouvement horizontal est dominant
        if ax >= ay:
            flip = dx < 0 if self.cote_face_droite else dx > 0
            return "S", flip

        # Direction verticale
        return ("D", False) if dy > 0 else ("U", False)


# Alias pour la compatibilité avec l'ancien code
DirectionalAnimator = AnimateurDirectionnel

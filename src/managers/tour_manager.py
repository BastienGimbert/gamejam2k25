import math
import os
from typing import TYPE_CHECKING, List, Tuple

import pygame

from classes.constants import ASSETS_DIR
from classes.position import Position
from classes.utils import distance_positions
from models.projectile import (
    EffetExplosion,
    ProjectileFleche,
    ProjectileMageEnnemi,
    ProjectilePierre,
    ProjectileTourMage,
)
from models.tour import Archer, Campement, Catapulte
from models.tour import Mage as TourMage
from models.tour import Tour

if TYPE_CHECKING:
    from game import Game


class TourManager:
    """Manager pour gérer tous les aspects liés aux tours."""

    def __init__(self, game: "Game"):
        self.game = game
        self.tours: List[Tour] = []
        self.projectiles: List = []
        self.effets_explosion: List[EffetExplosion] = []

        # Gestion des positions occupées par les tours
        self.positions_occupees: dict[tuple[int, int], dict] = {}

        # Gestion de la sélection des tours
        self.tour_selectionnee: tuple[int, int] | None = None

        # Prix par type de tour (affichage et logique d'achat/vente)
        self.prix_par_type: dict[str, int] = {
            "archer": getattr(Archer, "PRIX"),
            "catapulte": getattr(Catapulte, "PRIX"),
            "mage": getattr(TourMage, "PRIX"),
            "campement": getattr(Campement, "PRIX"),
        }

        # Portée par type de tour
        self.portee_par_type: dict[str, float] = {
            "archer": getattr(Archer, "PORTEE"),
            "catapulte": getattr(Catapulte, "PORTEE"),
            "mage": getattr(TourMage, "PORTEE"),
            "campement": getattr(Campement, "PORTEE"),
        }

        # Images de base des projectiles (chargées via une fonction générique)
        self.image_fleche = self._charger_image_projectile(
            ProjectileFleche.CHEMIN_IMAGE
        )
        self.image_pierre = self._charger_image_projectile(
            ProjectilePierre.CHEMIN_IMAGE
        )
        self.image_orbe_mage = self._charger_image_projectile(
            ProjectileTourMage.CHEMIN_IMAGE
        )
        self.image_projectileMageEnnemi = self._charger_image_projectile(
            ProjectileMageEnnemi.CHEMIN_IMAGE
        )

    def _charger_image_projectile(self, chemin_relatif: str):
        """Charge une image de projectile en utilisant la fonction utilitaire."""
        from classes.sprites import charger_image_projectile

        return charger_image_projectile(chemin_relatif)

    def ajouter_tour(self, tour: Tour) -> None:
        """Ajoute une tour à la liste des tours."""
        self.tours.append(tour)

    def retirer_tour(self, tour: Tour) -> None:
        """Retire une tour de la liste des tours."""
        if tour in self.tours:
            self.tours.remove(tour)

    def retirer_tour_par_position(self, position: Position) -> None:
        """Retire une tour à une position donnée."""
        self.tours = [
            t
            for t in self.tours
            if not (
                int(t.position.x) == int(position.x)
                and int(t.position.y) == int(position.y)
            )
        ]

    def get_tours_feu_de_camp(self) -> List[Campement]:
        """Retourne toutes les tours de type Campement."""
        return [t for t in self.tours if isinstance(t, Campement)]

    def dans_feu_de_camp(self, position: Position) -> bool:
        """Vérifie si une position est dans la portée d'un feu de camp."""
        for t in self.get_tours_feu_de_camp():
            if distance_positions(t.position, position) <= t.portee:
                return True
        return False

    def mettre_a_jour_tours(self, dt: float, ennemis_actifs: List) -> None:
        """Met à jour toutes les tours (acquisition cible + tir)."""
        for t in self.tours:
            if isinstance(t, Campement):
                continue

            def au_tir(tour: Tour, cible):
                if isinstance(tour, Archer) and self.image_fleche is not None:
                    p = ProjectileFleche(
                        origine=tour.position, cible_pos=cible.position.copy()
                    )
                    p.cible = cible  # suivi de la cible (comme une flèche)
                    p.image_base = self.image_fleche
                    self.projectiles.append(p)
                    # Joue le son de flèche
                    self.game.jouer_sfx("arrow.mp3", volume=0.1)

                elif isinstance(tour, Catapulte) and self.image_pierre is not None:
                    p = ProjectilePierre(
                        origine=tour.position,
                        cible_pos=cible.position.copy(),
                        game_ref=self.game,
                    )
                    p.cible = cible
                    p.image_base = self.image_pierre
                    self.projectiles.append(p)
                    # Joue le son de catapulte
                    self.game.jouer_sfx("catapult.mp3", volume=0.3)

                    # Déclenche la réaction du mage le plus proche pour intercepter la pierre
                    mage = self.game.get_closest_mage(p.position)
                    if (
                        mage is not None
                        and getattr(self, "image_projectileMageEnnemi", None)
                        is not None
                    ):
                        mage.react_to_projectile()
                        pm = ProjectileMageEnnemi(
                            origine=mage.position.copy(), cible_proj=p, vitesse=700.0
                        )
                        pm.image_base = self.image_projectileMageEnnemi
                        self.projectiles.append(pm)

                elif isinstance(tour, TourMage) and self.image_orbe_mage is not None:
                    # LOGIQUE SIMPLE identique à l'archer (pas d'interception ici)
                    p = ProjectileTourMage(
                        origine=tour.position, cible_pos=cible.position.copy()
                    )
                    p.cible = cible
                    p.image_base = self.image_orbe_mage
                    self.projectiles.append(p)
                    # Joue le son du mage
                    self.game.jouer_sfx("fire-magic.mp3", volume=0.2)

            if hasattr(t, "maj"):
                t.maj(dt, ennemis_actifs, au_tir=au_tir)

    def mettre_a_jour_projectiles(self, dt: float, ennemis_actifs: List) -> None:
        """Met à jour tous les projectiles et gère les collisions."""
        for pr in self.projectiles:
            if hasattr(pr, "mettreAJour"):
                pr.mettreAJour(dt)
            if getattr(pr, "detruit", False):
                continue

            if not isinstance(pr, ProjectileMageEnnemi):
                # Collision projectiles tours -> ennemis
                for e in ennemis_actifs:
                    if hasattr(pr, "aTouche") and pr.aTouche(e):
                        if hasattr(pr, "appliquerDegats"):
                            # Gestion spéciale pour les projectiles de mage avec dégâts de zone
                            if isinstance(pr, ProjectileTourMage):
                                # Appliquer les dégâts de zone à tous les ennemis dans la zone
                                pr.appliquerDegatsZone(ennemis_actifs)
                                # Marquer le projectile comme détruit
                                pr.detruit = True
                                # Créer un effet d'explosion visuel
                                effet = EffetExplosion(
                                    pr.x, pr.y, pr.rayon_zone_effet, 0.6
                                )
                                self.effets_explosion.append(effet)
                                # Son d'explosion magique
                                self.game.jouer_sfx("explosion-pierre.mp3", volume=0.3)
                            else:
                                # Comportement normal pour les autres projectiles
                                pr.appliquerDegats(e)
                                if (
                                    isinstance(pr, ProjectileFleche)
                                    and hasattr(e, "__class__")
                                    and "Chevalier" in str(e.__class__)
                                ):
                                    self.game.jouer_sfx(
                                        "arrow-hit-metal.mp3", volume=0.5
                                    )

                            # Gestion des récompenses pour tous les ennemis morts
                            self.game.ennemi_manager.gerer_collisions_projectiles([pr])
                        break
            else:
                # Collision spécifique projectile mage ennemi -> projectile de catapulte
                cible = getattr(pr, "cible_proj", None)
                if cible and hasattr(pr, "aTouche") and pr.aTouche(cible):
                    self.game.jouer_sfx("explosion-pierre.mp3", volume=0.5)
                    cible.detruit = True
                    pr.detruit = True

        # Mise à jour des effets d'explosion
        for effet in self.effets_explosion:
            effet.mettre_a_jour(dt)

        # Nettoyage des effets d'explosion terminés
        self.effets_explosion = [
            effet for effet in self.effets_explosion if effet.actif
        ]

        # Nettoyage projectiles
        self.projectiles = [
            p for p in self.projectiles if not getattr(p, "detruit", False)
        ]

    def mettre_a_jour_feux_de_camps(
        self, dt: float, nuit_surface: pygame.Surface | None = None
    ) -> None:
        """Met à jour et dessine les effets de lumière des feux de camps."""
        feux_de_camps = [t for t in self.tours if t.__class__.__name__ == "Campement"]
        for feu in feux_de_camps:
            feu.maj(dt)
            if nuit_surface is not None:
                radius = feu.portee
                pygame.draw.circle(
                    nuit_surface, (0, 0, 0, 0), (feu.position.x, feu.position.y), radius
                )

    def dessiner_personnages_tours(self, ecran: pygame.Surface) -> None:
        """Dessine les personnages des tours."""
        for t in self.tours:
            t.draw_person(ecran)

    def dessiner_projectiles(self, ecran: pygame.Surface) -> None:
        """Dessine tous les projectiles."""
        for pr in self.projectiles:
            if hasattr(pr, "dessiner"):
                pr.dessiner(ecran)

    def dessiner_effets_explosion(self, ecran: pygame.Surface) -> None:
        """Dessine tous les effets d'explosion."""
        for effet in self.effets_explosion:
            effet.dessiner(ecran)

    def dessiner_range_tour(
        self,
        ecran: pygame.Surface,
        tour_selectionnee: Tuple[int, int] | None,
        taille_case: int,
    ) -> None:
        """Dessine la portée d'une tour sélectionnée."""
        if not tour_selectionnee:
            return

        x_case, y_case = tour_selectionnee

        # Cherche la tour correspondante
        tour = None
        cx = x_case * taille_case + taille_case // 2
        cy = y_case * taille_case + taille_case // 2
        for t in self.tours:
            if int(t.position.x) == cx and int(t.position.y) == cy:
                tour = t
                break

        if tour and hasattr(tour, "portee"):
            portee = getattr(tour, "portee", 120)

            # Dessine un cercle
            dash_count = 15  # nombre de segments
            dash_length = 0.15  # en radians

            for i in range(dash_count):
                angle_start = 2 * math.pi * i / dash_count
                angle_end = angle_start + dash_length
                x1 = int(cx + portee * math.cos(angle_start))
                y1 = int(cy + portee * math.sin(angle_start))
                x2 = int(cx + portee * math.cos(angle_end))
                y2 = int(cy + portee * math.sin(angle_end))
                pygame.draw.line(ecran, (255, 255, 255), (x1, y1), (x2, y2), 3)

    def creer_tour(
        self, type_tour: str, position: Position, tour_id: int
    ) -> Tour | None:
        """Crée une nouvelle tour selon le type spécifié."""
        if type_tour == "archer":
            return Archer(id=tour_id, position=position)
        elif type_tour == "catapulte":
            return Catapulte(id=tour_id, position=position)
        elif type_tour == "mage":
            return TourMage(id=tour_id, position=position)
        elif type_tour == "campement":
            return Campement(id=tour_id, position=position)
        else:
            return None

    def peut_placer_tour(
        self, case: tuple[int, int], type_tour: str, cases_bannies: set
    ) -> bool:
        """Vérifie si une tour peut être placée à la case donnée."""
        return (
            case not in self.positions_occupees
            and self.game.joueur.argent >= self.prix_par_type.get(type_tour, 0)
            and case not in cases_bannies
        )

    def placer_tour(self, case: tuple[int, int], type_tour: str) -> bool:
        """Place une tour à la case donnée."""
        if not self.peut_placer_tour(case, type_tour, self.game.cases_bannies):
            return False

        # 1) Marque la case occupée (affichage)
        self.positions_occupees[case] = {
            "type": type_tour,
            "frame": 0,
        }

        # 2) Crée l'instance de tour
        x_case, y_case = case
        cx = x_case * self.game.taille_case + self.game.taille_case // 2
        cy = y_case * self.game.taille_case + self.game.taille_case // 2
        pos_tour = Position(cx, cy)
        tour_id = len(self.tours) + 1
        nouvelle_tour = self.creer_tour(type_tour, pos_tour, tour_id)

        if nouvelle_tour is not None:
            self.ajouter_tour(nouvelle_tour)
            self.positions_occupees[case]["instance"] = nouvelle_tour

            # Joue le son du campement si c'est un campement
            if type_tour == "campement":
                try:
                    campfire_sound = pygame.mixer.Sound(
                        os.path.join(ASSETS_DIR, "audio", "bruitage", "camp-fire.mp3")
                    )
                    campfire_sound.play().set_volume(0.15)
                except Exception:
                    pass

            # Mémorise le prix d'achat pour revente éventuelle
            self.positions_occupees[case]["prix"] = self.prix_par_type.get(type_tour, 0)
            self.positions_occupees[case]["type_selectionne"] = type_tour

            # Débiter le prix correspondant
            self.game.joueur.argent -= self.prix_par_type.get(type_tour, 0)

            # Augmente les prix à chaque achat
            self._augmenter_prix_apres_achat(type_tour)

            return True
        return False

    def vendre_tour(self, case: tuple[int, int]) -> bool:
        """Vend une tour à la case donnée."""
        if case not in self.positions_occupees:
            return False

        # Prix payé mémorisé au placement; remboursement = moitié (arrondi bas)
        prix_achat = int(self.positions_occupees[case].get("prix", 0))
        remboursement = prix_achat // 2
        self.game.joueur.argent += remboursement

        # Rebaisse le prix de la tour à chaque vente
        self._diminuer_prix_apres_vente(case)

        # Retire l'instance de tour à cet emplacement (centre de case)
        cx = case[0] * self.game.taille_case + self.game.taille_case // 2
        cy = case[1] * self.game.taille_case + self.game.taille_case // 2
        pos_tour = Position(cx, cy)
        self.retirer_tour_par_position(pos_tour)

        # Libère la case pour placement futur
        del self.positions_occupees[case]

        return True

    def _augmenter_prix_apres_achat(self, type_tour: str) -> None:
        """Augmente le prix d'une tour après achat."""
        if type_tour == "campement":
            self.prix_par_type["campement"] = int(self.prix_par_type["campement"] * 1.5)
        elif type_tour == "archer":
            self.prix_par_type["archer"] = int(self.prix_par_type["archer"] + 2)
        elif type_tour == "catapulte":
            self.prix_par_type["catapulte"] = int(self.prix_par_type["catapulte"] + 5)
        elif type_tour == "mage":
            self.prix_par_type["mage"] = int(self.prix_par_type["mage"] * 1.5)

    def _diminuer_prix_apres_vente(self, case: tuple[int, int]) -> None:
        """Diminue le prix d'une tour après vente."""
        type_tour = self.positions_occupees[case]["type_selectionne"]

        if type_tour == "campement":
            self.prix_par_type["campement"] = int(
                round(self.prix_par_type["campement"] * 0.6666)
            )
        elif type_tour == "archer":
            self.prix_par_type["archer"] = max(5, int(self.prix_par_type["archer"] - 2))
        elif type_tour == "catapulte":
            self.prix_par_type["catapulte"] = max(
                10, int(self.prix_par_type["catapulte"] - 5)
            )
        elif type_tour == "mage":
            self.prix_par_type["mage"] = int(round(self.prix_par_type["mage"] * 0.6666))

    def selectionner_tour(self, case: tuple[int, int] | None) -> None:
        """Sélectionne ou désélectionne une tour."""
        if case and case in self.positions_occupees:
            if self.tour_selectionnee == case:
                self.tour_selectionnee = None  # désélectionne si déjà sélectionnée
            else:
                self.tour_selectionnee = case  # sélectionne la tour
        else:
            self.tour_selectionnee = None  # désélectionne si on clique ailleurs

    def dessiner_tours_placees(self, ecran: pygame.Surface, taille_case: int) -> None:
        """Dessine les tours placées, avec un traitement spécial pour Campement."""
        for (x_case, y_case), data in self.positions_occupees.items():
            tour = data.get("instance")

            if tour and hasattr(tour, "dessiner"):
                # Campement (et éventuellement d'autres tours spéciales)
                tour.dessiner(ecran, taille_case)
            else:
                # Cas standard (anciennes tours fixes)
                ttype = data["type"]
                surf = None
                if (
                    ttype in self.game.tower_assets
                    and self.game.tower_assets[ttype]["frames"]
                ):
                    slices = self.game.tower_assets[ttype]["frames"][0]
                    surf = slices[2]
                    surf = pygame.transform.smoothscale(
                        surf, (taille_case, taille_case)
                    )
                if surf is None:
                    surf = pygame.Surface((taille_case, taille_case))
                    surf.fill((150, 150, 180))
                ecran.blit(surf, (x_case * taille_case, y_case * taille_case))

        # --- Ajout : affichage range si sélectionnée ---
        if self.tour_selectionnee:
            self.dessiner_range_tour(ecran, self.tour_selectionnee, taille_case)

    def reset(self) -> None:
        """Remet le manager à zéro."""
        self.tours = []
        self.projectiles = []
        self.effets_explosion = []
        self.positions_occupees = {}
        self.tour_selectionnee = None

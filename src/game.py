from __future__ import annotations

import math
import os

import pygame

from classes.bouton import Bouton
from classes.constants import (
    ASSETS_DIR,
    AUDIO_DIR,
    COIN_ANIM_INTERVAL_MS,
    DEFAULT_TOWER_TYPES,
    GAME_HEIGHT,
    GAME_WIDTH,
    GRID_COLS,
    GRID_ROWS,
    HEART_ANIM_INTERVAL_MS,
    HEART_DIR,
    MAP_PNG,
    MAP_TILESET_TMJ,
    MONEY_DIR,
    PROJECT_ROOT,
    RECOMPENSES_PAR_VAGUE,
    SHOP_WIDTH,
    SPELLS_HEIGHT,
    TILE_SIZE,
    TOWER_DIR,
    WINDOW_HEIGHT,
)
from classes.pointeur import Pointeur
from classes.position import Position
from classes.sprites import (
    charger_animation_ui,
    charger_image_assets,
    charger_image_avec_redimensionnement,
    charger_image_projectile,
    charger_sprites_tour_assets,
    charger_spritesheet_ui,
    decouper_sprite,
)
from classes.utils import (
    case_depuis_pos,
    cases_depuis_chemin,
    charger_chemin_tiled,
    distance_positions,
    position_dans_grille,
)
from managers.audio_manager import AudioManager
from managers.ennemi_manager import EnnemiManager
from managers.shop_manager import ShopManager
from managers.tour_manager import TourManager
from managers.ui_manager import UIManager
from models.ennemi import Chevalier, Ennemi, Gobelin, Mage
from models.joueur import Joueur
from models.sort import SortEclair, SortFee, SortVision

# Import nécessaire pour le type hint
from models.tour import Campement


class Game:

    def __init__(self, police: pygame.font.Font, est_muet: bool = False):
        self.joueur = Joueur(argent=45, point_de_vie=100)

        # Gestion des vagues
        # Manager des ennemis
        self.ennemi_manager = EnnemiManager(self)

        # Manager des tours
        self.tour_manager = TourManager(self)

        self.police = police
        self.police_tour = pygame.font.Font(None, 44)
        # self.est_muet = est_muet
        # self._sons_cache: dict[str, pygame.mixer.Sound] = {}
        self.couleurs = {
            "fond": (0, 6, 25),
            "bordure": (40, 40, 60),
            "texte": (200, 220, 255),
        }

        # Grille / carte
        self.taille_case = TILE_SIZE
        self.colonnes = GRID_COLS
        self.lignes = GRID_ROWS
        self.largeur_ecran = GAME_WIDTH
        self.hauteur_ecran = GAME_HEIGHT  # Taille normale de la carte
        self.case_survolee: tuple[int, int] | None = None

        # Sorts du joueur
        self.sorts = {
            "vision": SortVision(niveau=1),
            "fee": SortFee(niveau=1),
            "eclair": SortEclair(niveau=1),
        }

        # État de sélection des sorts
        self.eclair_selectionne = False

        # Types de tours
        self.tower_types = DEFAULT_TOWER_TYPES

        self.tower_assets = self._charger_tours()

        # Manager de la boutique (après la définition des types de tours et assets)
        self.shop_manager = ShopManager(self)

        # Manager audio
        self.audio_manager = AudioManager(self)
        self.audio_manager.set_muet(est_muet)

        # Manager UI
        self.ui_manager = UIManager(self)

        medieval_couleurs = {
            "fond_normal": (110, 70, 30),  # brun
            "fond_survol": (150, 100, 40),  # brun clair
            "contour": (220, 180, 60),  # doré
            "texte": (240, 220, 180),  # beige
        }
        police_medievale = pygame.font.Font(None, 38)
        self.bouton_vague = Bouton(
            "Lancer la vague",
            self.shop_manager.rect_boutique.x + 20,
            self.hauteur_ecran - 70,
            self.shop_manager.largeur_boutique - 40,
            50,
            self.ennemi_manager.lancer_vague,
            police_medievale,
            medieval_couleurs,
        )

        self.type_selectionne: str | None = None

        self.couleur_boutique_bg = (30, 30, 30)
        self.couleur_boutique_border = (80, 80, 80)
        self.couleur_bouton_bg = (60, 60, 60)
        self.couleur_bouton_hover = (90, 90, 90)
        self.couleur_texte = (240, 240, 240)

        # Couleurs pour la boutique de sorts (même style que la boutique)
        self.couleur_boutique_sorts_bg = self.couleur_boutique_bg
        self.couleur_boutique_sorts_border = self.couleur_boutique_border

        # Carte / chemin
        self.clock = pygame.time.Clock()
        self.carte = self._charger_carte()
        self.tmj_path = MAP_TILESET_TMJ
        chemin_positions = charger_chemin_tiled(self.tmj_path, layer_name="path")
        self.cases_bannies = cases_depuis_chemin(chemin_positions, self.taille_case)
        # Bannir aussi les 6 cases des deux premières lignes (x=0..5, y=0..1)
        for y in (0, 1):
            for x in range(0, 6):
                if 0 <= x < self.colonnes and 0 <= y < self.lignes:
                    self.cases_bannies.add((x, y))

        # Pointeur
        self.pointeur = Pointeur()

    # ---------- Chargements ----------
    def _charger_carte(self):
        """Charge la carte en utilisant la fonction utilitaire."""
        img = charger_image_assets(MAP_PNG.split("/")[-1], "tilesets")
        if img is None:
            raise FileNotFoundError(f"Carte non trouvée: {MAP_PNG}")
        return img

    def _charger_tours(self):
        """Charge tous les assets des tours en utilisant la fonction utilitaire."""
        assets = {}
        for tower_type in self.tower_types:
            assets[tower_type] = charger_sprites_tour_assets(tower_type)
        return assets

    def _dessiner_personnages_tours(self, ecran):
        self.tour_manager.dessiner_personnages_tours(ecran)

    # ---------- Update / boucle ----------
    def maj(self, dt: float):
        # Mise à jour du manager d'ennemis et des vagues
        self.ennemi_manager.mettre_a_jour_vague()
        self.ennemi_manager.mettre_a_jour_ennemis(dt)

        # Appliquer les effets des sorts
        for sort in self.sorts.values():
            sort.appliquer_effet(self)

        # Mettre à jour la visibilité des ennemis (après les sorts)
        for ennemi in self.ennemi_manager.get_ennemis_actifs():
            if hasattr(ennemi, "majVisible"):
                ennemi.majVisible(self)

        # Mise à jour des tours (acquisition cible + tir)
        self.tour_manager.mettre_a_jour_tours(
            dt, self.ennemi_manager.get_ennemis_actifs()
        )

        # Mise à jour des projectiles + collisions
        self.tour_manager.mettre_a_jour_projectiles(
            dt, self.ennemi_manager.get_ennemis_actifs()
        )

        # Nettoyage ennemis
        self.ennemi_manager.nettoyer_ennemis_morts()

        # Gérer la fin de vague (récompenses, nuit, etc.)
        self.ennemi_manager.gerer_fin_vague()

    def get_closest_mage(self, pos: Position) -> None | Mage:
        """Retourne le mage le plus proche de la position pos."""
        mages = [
            e for e in self.ennemi_manager.get_mages_actifs() if e.ready_to_attack()
        ]
        if not mages:
            return None
        nearestMage = mages[0]
        distance = distance_positions(nearestMage.position, pos)
        for m in mages:
            if distance_positions(m.position, pos) < distance:
                nearestMage = m
                distance = distance_positions(m.position, pos)

        return nearestMage

    def majFeuxDeCamps(
        self, dt: float, nuit_surface: pygame.Surface | None = None
    ) -> None:
        """Met à jour et dessine les effets de lumière des feux de camps."""
        self.tour_manager.mettre_a_jour_feux_de_camps(dt, nuit_surface)

    # def get_max_vague_csv(self) -> int:
    #     return self.ennemi_manager.get_max_vague_csv()

    def dessiner(self, ecran: pygame.Surface) -> None:
        if self.ennemi_manager.est_victoire():
            self.ui_manager.dessiner_victoire(ecran)
            return

        dt = self.clock.tick(60) / 1000.0

        # Délégation complète du rendu à l'UIManager
        self.ui_manager.dessiner_interface_jeu(ecran, dt)

        # self.pointeur.draw(ecran, self)  # Désactivé pour enlever le filtre bleu
        self.maj(dt)

    def jouer_sfx(self, fichier: str, volume: float = 1.0) -> None:
        """Joue un son ponctuel via l'AudioManager."""
        self.audio_manager.jouer_sfx(fichier, volume)

    def decompte_dt(self) -> None:
        dt = self.clock.tick(60) / 1000.0

    # ---------- Evénements ----------
    def gerer_evenement(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # Annuler la sélection d'éclair si elle est active
            if hasattr(self, "eclair_selectionne") and self.eclair_selectionne:
                self.eclair_selectionne = False
                return None
            return "PAUSE"

        if event.type == pygame.MOUSEMOTION:
            pos = pygame.mouse.get_pos()
            if position_dans_grille(pos, self.largeur_ecran, self.hauteur_ecran):
                self.case_survolee = case_depuis_pos(
                    pos, self.taille_case, self.colonnes, self.lignes
                )
            else:
                self.case_survolee = None

        # Clic gauche: sélection dans la boutique et placement d'une tour
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            # Vérifier si l'éclair est sélectionné et cliquer sur une case
            if hasattr(self, "eclair_selectionne") and self.eclair_selectionne:
                if position_dans_grille(pos, self.largeur_ecran, self.hauteur_ecran):
                    case = case_depuis_pos(
                        pos, self.taille_case, self.colonnes, self.lignes
                    )
                    if case and case in getattr(self, "cases_bannies", set()):
                        # L'éclair ne peut être utilisé que sur les cases du chemin
                        # Mais pas sur les 6 cases en haut à gauche (x=0..5, y=0..1)
                        x_case, y_case = case
                        if (x_case, y_case) in [
                            (x, y) for y in (0, 1) for x in range(0, 6)
                        ]:
                            return None
                        # Activer l'éclair sur cette case
                        if self.sorts["eclair"].activer_sur_case(x_case, y_case):
                            # Son d'éclair (respecte muet)
                            self.jouer_sfx("loud-thunder.mp3")
                            # Débiter le prix
                            self.joueur.argent -= self.sorts["eclair"].prix
                            # Désélectionner l'éclair
                            self.eclair_selectionne = False
                        return None
            # Clic dans la boutique de sorts
            if self.shop_manager.gerer_clic_boutique_sorts(pos):
                return None
            # Clic dans la boutique des tours
            if (
                self.bouton_vague.rect.collidepoint(pos)
                and self.ennemi_manager.vague_terminee()
            ):
                self.bouton_vague.action()
                self.tour_manager.tour_selectionnee = None  # désélectionne la range
                return None
            if self.shop_manager.gerer_clic_boutique_tours(pos):
                self.tour_manager.tour_selectionnee = None  # désélectionne la range
                return None

            # Placement de tour (priorité sur la sélection)
            if self.type_selectionne and position_dans_grille(
                pos, self.largeur_ecran, self.hauteur_ecran
            ):
                case = case_depuis_pos(
                    pos, self.taille_case, self.colonnes, self.lignes
                )
                if case and self.tour_manager.peut_placer_tour(
                    case, self.type_selectionne, self.cases_bannies
                ):
                    if self.tour_manager.placer_tour(case, self.type_selectionne):
                        self.type_selectionne = None
                        self.tour_manager.tour_selectionnee = (
                            None  # désélectionne la range
                        )
                return None

            # --- Ajout : sélection/désélection d'une tour placée pour afficher la range ---
            if position_dans_grille(pos, self.largeur_ecran, self.hauteur_ecran):
                case = case_depuis_pos(
                    pos, self.taille_case, self.colonnes, self.lignes
                )
                self.tour_manager.selectionner_tour(case)
                return None

        # Clic droit: vendre une tour posée (si on clique sur une case occupée)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            pos = event.pos
            # On ignore si on clique dans la zone boutique
            if self.shop_manager.rect_boutique.collidepoint(pos):
                self.tour_manager.tour_selectionnee = None  # désélectionne la range
                return None
            if position_dans_grille(pos, self.largeur_ecran, self.hauteur_ecran):
                case = case_depuis_pos(
                    pos, self.taille_case, self.colonnes, self.lignes
                )
                if case and case in self.tour_manager.positions_occupees:
                    self.tour_manager.vendre_tour(case)
                    self.tour_manager.tour_selectionnee = None  # désélectionne la range

        return None

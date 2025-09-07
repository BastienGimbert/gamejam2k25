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
from classes.ennemi import Chevalier, Ennemi, Gobelin, Mage
from classes.ennemi_manager import EnnemiManager
from classes.tour_manager import TourManager
from classes.shop_manager import ShopManager
from classes.joueur import Joueur
from classes.pointeur import Pointeur
from classes.position import Position
# Les projectiles sont maintenant gérés par TourManager
# from classes.projectile import (
#     EffetExplosion,
#     ProjectileFleche,
#     ProjectileMageEnnemi,
#     ProjectilePierre,
#     ProjectileTourMage,
# )
from classes.sort import SortEclair, SortFee, SortVision
# Les tours sont maintenant gérées par TourManager
# from classes.tour import Archer, Campement, Catapulte
# from classes.tour import Mage as TourMage
# from classes.tour import Tour

# Import nécessaire pour le type hint
from classes.tour import Campement
from classes.sprites import (
    charger_animation_ui,
    charger_image_assets,
    charger_image_avec_redimensionnement,
    charger_image_projectile,
    charger_sprites_tour_assets,
    charger_spritesheet_ui,
    decouper_sprite,
)
from classes.utils import charger_chemin_tiled, distance_positions


class Game:
    def afficher_victoire(self, ecran):
        img = charger_image_avec_redimensionnement(
            "assets/VICTOIRE.png", 
            (ecran.get_width(), ecran.get_height())
        )
        if img:
            ecran.blit(img, (0, 0))
        
    def __init__(self, police: pygame.font.Font, est_muet: bool = False):
        self.joueur = Joueur(argent=450, point_de_vie=100, sort="feu", etat="normal")

        # Gestion des vagues
        # Manager des ennemis
        self.ennemi_manager = EnnemiManager(self)
        
        # Manager des tours
        self.tour_manager = TourManager(self)

        self.police = police
        self.police_tour = pygame.font.Font(None, 44)
        # État muet propagé depuis main
        self.est_muet = est_muet
        # Cache de sons ponctuels
        self._sons_cache: dict[str, pygame.mixer.Sound] = {}
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

        # Boutique (à droite de la carte) - maintenant géré par ShopManager
        # self.largeur_boutique = SHOP_WIDTH
        # self.rect_boutique = pygame.Rect(
        #     self.largeur_ecran, 0, self.largeur_boutique, self.hauteur_ecran
        # )

        # Boutique de sorts (en bas de l'écran) - maintenant géré par ShopManager
        # self.hauteur_boutique_sorts = SPELLS_HEIGHT
        # self.rect_boutique_sorts = pygame.Rect(
        #     0, self.hauteur_ecran, self.largeur_ecran + self.largeur_boutique, self.hauteur_boutique_sorts
        # )

        # Sorts du joueur
        self.sorts = {
            "vision": SortVision(niveau=1),
            "fee": SortFee(niveau=1),
            "eclair": SortEclair(niveau=1),
        }

        # État de sélection des sorts
        self.eclair_selectionne = False
        # Prix par type de tour (affichage et logique d'achat/vente) - maintenant géré par TourManager
        # self.prix_par_type: dict[str, int] = {
        #     "archer": getattr(Archer, "PRIX"),
        #     "catapulte": getattr(Catapulte, "PRIX"),
        #     "mage": getattr(TourMage, "PRIX"),
        #     "campement": getattr(Campement, "PRIX"),
        # }

        # Portée par type de tour - maintenant géré par TourManager
        # self.portee_par_type: dict[str, float] = {
        #     "archer": getattr(Archer, "PORTEE"),
        #     "catapulte": getattr(Catapulte, "PORTEE"),
        #     "mage": getattr(TourMage, "PORTEE"),
        #     "campement": getattr(Campement, "PORTEE"),
        # }

        # Animation monnaie - maintenant géré par ShopManager
        # self.coin_frames = self._charger_piece()
        # self.coin_frame_idx = 0
        # self.COIN_ANIM_INTERVAL = COIN_ANIM_INTERVAL_MS
        # self.last_coin_ticks = pygame.time.get_ticks()

        # Animation coeurs (PV) - maintenant géré par ShopManager
        # self.heart_frames = self._charger_coeurs()
        # self.heart_frame_idx = 0
        # self.HEART_ANIM_INTERVAL = HEART_ANIM_INTERVAL_MS
        # self.last_heart_ticks = pygame.time.get_ticks()

        # Types de tours
        self.tower_types = DEFAULT_TOWER_TYPES
        # --- Ajout : sélection de tour pour affichage de la range - maintenant géré par TourManager ---
        # self.tour_selectionnee: tuple[int, int] | None = None

        self.tower_assets = self._charger_tours()
        # self.shop_items = self._creer_boutons_boutique()  # maintenant géré par ShopManager
        
        # Manager de la boutique (après la définition des types de tours et assets)
        self.shop_manager = ShopManager(self)
        
        # Créer le bouton de vague maintenant que le ShopManager est initialisé
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
            self.lancerVague,
            police_medievale,
            medieval_couleurs,
        )
        
        self.type_selectionne: str | None = None

        # Occupation des cases (affichage) - maintenant géré par TourManager
        # self.positions_occupees: dict[tuple[int, int], dict] = {}

        # Tours / projectiles (logique) - maintenant gérés par TourManager
        # self.tours: list[Tour] = []
        # self.projectiles: list[
        #     ProjectileFleche | ProjectilePierre | ProjectileTourMage
        # ] = []
        # 
        # # Effets visuels d'explosion
        # self.effets_explosion: list[EffetExplosion] = []

        # Couleurs UI - maintenant gérées par ShopManager
        # self.couleur_boutique_bg = (30, 30, 30)
        # self.couleur_boutique_border = (80, 80, 80)
        # self.couleur_bouton_bg = (60, 60, 60)
        # self.couleur_bouton_hover = (90, 90, 90)
        # self.couleur_texte = (240, 240, 240)

        # Couleurs pour la boutique de sorts (même style que la boutique) - maintenant gérées par ShopManager
        # self.couleur_boutique_sorts_bg = self.couleur_boutique_bg
        # self.couleur_boutique_sorts_border = self.couleur_boutique_border

        self.couleur_quadrillage = (40, 60, 100)
        self.couleur_surbrillance = (80, 180, 255)
        self.couleur_surbrillance_interdite = (255, 80, 80)
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
        self.cases_bannies = self._cases_depuis_chemin(chemin_positions)
        # Bannir aussi les 6 cases des deux premières lignes (x=0..5, y=0..1)
        for y in (0, 1):
            for x in range(0, 6):
                if 0 <= x < self.colonnes and 0 <= y < self.lignes:
                    self.cases_bannies.add((x, y))

        # Pointeur
        self.pointeur = Pointeur()

        # État jour/nuit - maintenant géré par EnnemiManager
        # self.est_nuit = False

        # self.action_bouton= self.lancerVague()
        # self.bouton = Bouton("Bouton", 100, 100, 200, 50, self.action_bouton, self.police, self.couleurs)

    def getToursFeuDeCamp(self) -> list[Campement]:
        return self.tour_manager.get_tours_feu_de_camp()

    def dansFeuDeCamp(self, position: Position) -> bool:
        return self.tour_manager.dans_feu_de_camp(position)


    # ---------- Chargements ----------
    def _charger_carte(self):
        """Charge la carte en utilisant la fonction utilitaire."""
        img = charger_image_assets(MAP_PNG.split('/')[-1], "tilesets")
        if img is None:
            raise FileNotFoundError(f"Carte non trouvée: {MAP_PNG}")
        return img

    # def _charger_piece(self):
    #     """Charge l'animation des pièces depuis MonedaD.png (spritesheet)."""
    #     coinImg = os.path.join(MONEY_DIR, "MonedaD.png")
    #     frames = charger_spritesheet_ui(coinImg, 5, scale=1.0)
    #     # Redimensionner à 24x24
    #     if frames:
    #         frames = [pygame.transform.smoothscale(f, (24, 24)) for f in frames]
    #     return frames

    # def _charger_coeurs(self):
    #     """Charge toutes les images de coeur en utilisant la fonction utilitaire."""
    #     return charger_animation_ui("heart", scale=1.0)

    def _charger_tours(self):
        """Charge tous les assets des tours en utilisant la fonction utilitaire."""
        assets = {}
        for tower_type in self.tower_types:
            assets[tower_type] = charger_sprites_tour_assets(tower_type)
        return assets

    # def _creer_boutons_boutique(self):
    #     boutons = []
    #     x = self.rect_boutique.x + 20
    #     y = 100
    #     espace_y = 90
    #     for t in self.tower_types:
    #         rect = pygame.Rect(x, y, self.largeur_boutique - 40, 70)
    #         boutons.append({"type": t, "rect": rect})
    #         y += espace_y
    #     return boutons

    # def _charger_image_projectile(self, chemin_relatif: str):
    #     """Charge une image de projectile en utilisant la fonction utilitaire."""
    #     return charger_image_projectile(chemin_relatif)

    # ---------- Utilitaires ----------

    def _position_dans_grille(self, pos):
        return pos[0] < self.largeur_ecran and 0 <= pos[1] < self.hauteur_ecran

    def _case_depuis_pos(self, pos):
        x_case = pos[0] // self.taille_case
        y_case = pos[1] // self.taille_case
        if 0 <= x_case < self.colonnes and 0 <= y_case < self.lignes:
            return (x_case, y_case)
        return None

    def _dessiner_quadrillage(self, ecran):
        largeur_draw = self.largeur_ecran
        for x in range(0, largeur_draw + 1, self.taille_case):
            pygame.draw.line(
                ecran, self.couleur_quadrillage, (x, 0), (x, self.hauteur_ecran)
            )
        for y in range(0, self.hauteur_ecran + 1, self.taille_case):
            pygame.draw.line(ecran, self.couleur_quadrillage, (0, y), (largeur_draw, y))

    def _dessiner_personnages_tours(self, ecran):
        self.tour_manager.dessiner_personnages_tours(ecran)

    # Les méthodes de dessin de boutique sont maintenant dans ShopManager
    # def _dessiner_boutique(self, ecran): ...
    # def _dessiner_boutique_sorts(self, ecran): ...

    def _dessiner_surbrillance(self, ecran):
        # Surbrillance pour l'éclair (seulement sur les cases du chemin, sauf les 6 en haut à gauche)
        if (
            hasattr(self, "eclair_selectionne")
            and self.eclair_selectionne
            and self.case_survolee
        ):
            if self.case_survolee in getattr(
                self, "cases_bannies", set()
            ) and self.case_survolee not in [
                (x, y) for y in (0, 1) for x in range(0, 6)
            ]:
                x_case, y_case = self.case_survolee
                rect = pygame.Rect(
                    x_case * self.taille_case,
                    y_case * self.taille_case,
                    self.taille_case,
                    self.taille_case,
                )
                overlay = pygame.Surface(
                    (self.taille_case, self.taille_case), pygame.SRCALPHA
                )
                # Couleur jaune pour l'éclair
                overlay.fill((255, 255, 0, 100))
                if rect.right <= self.largeur_ecran:
                    ecran.blit(overlay, rect)
            return

        # Surbrillance pour les tours
        if not self.case_survolee or not self.type_selectionne:
            return

        x_case, y_case = self.case_survolee
        rect = pygame.Rect(
            x_case * self.taille_case,
            y_case * self.taille_case,
            self.taille_case,
            self.taille_case,
        )

        # Surbrillance
        overlay = pygame.Surface((self.taille_case, self.taille_case), pygame.SRCALPHA)
        interdit = (x_case, y_case) in getattr(self, "cases_bannies", set()) or (
            x_case,
            y_case,
        ) in self.tour_manager.positions_occupees
        couleur = (
            self.couleur_surbrillance_interdite
            if interdit
            else self.couleur_surbrillance
        )
        overlay.fill((*couleur, 80))
        if rect.right <= self.largeur_ecran:
            ecran.blit(overlay, rect)

        # Cercle autour de la case

        portee = self.tour_manager.portee_par_type.get(self.type_selectionne, 0)
        cx = x_case * self.taille_case + self.taille_case // 2
        cy = y_case * self.taille_case + self.taille_case // 2

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

    def _dessiner_tours_placees(self, ecran):
        """Dessine les tours, avec un traitement spécial pour Campement."""
        self.tour_manager.dessiner_tours_placees(ecran, self.taille_case)


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
        self.tour_manager.mettre_a_jour_tours(dt, self.ennemi_manager.get_ennemis_actifs())

        # Mise à jour des projectiles + collisions
        self.tour_manager.mettre_a_jour_projectiles(dt, self.ennemi_manager.get_ennemis_actifs())

        # Nettoyage ennemis
        self.ennemi_manager.nettoyer_ennemis_morts()

        # Gérer la fin de vague (récompenses, nuit, etc.)
        self.ennemi_manager.gerer_fin_vague()

    def get_closest_mage(self, pos: Position) -> None | Mage:
        """Retourne le mage le plus proche de la position pos."""
        mages = [
            e for e in self.ennemi_manager.get_mages_actifs() 
            if e.ready_to_attack()
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

    def majFeuxDeCamps(self, dt: float, nuit_surface: pygame.Surface | None = None) -> None:
        """Met à jour et dessine les effets de lumière des feux de camps."""
        self.tour_manager.mettre_a_jour_feux_de_camps(dt, nuit_surface)

    # def get_max_vague_csv(self) -> int:
    #     # Maintenant géré par EnnemiManager
    #     return self.ennemi_manager.get_max_vague_csv()  

    def dessiner(self, ecran: pygame.Surface) -> None:
        if self.ennemi_manager.est_victoire():
            self.afficher_victoire(ecran)
            return

        dt = self.clock.tick(60) / 1000.0
        ecran.blit(self.carte, (0, 0))
        self._dessiner_tours_placees(ecran)
        self._dessiner_personnages_tours(ecran)
        self._dessiner_surbrillance(ecran)

        # Effet nuit - seulement pendant les manches
        if self.ennemi_manager.est_nuit:
            nuit_surface = pygame.Surface(
                (self.largeur_ecran, self.hauteur_ecran), pygame.SRCALPHA
            )
            nuit_surface.fill((0, 6, 25, int(255 * 0.7)))  # 70% opacity

            # Vérifier si la fée est active
            if "fee" in self.sorts and self.sorts["fee"].est_actif():
                # Si la fée est active, éclairer toute la carte
                pygame.draw.circle(
                    nuit_surface,
                    (0, 0, 0, 0),
                    (self.largeur_ecran // 2, self.hauteur_ecran // 2),
                    max(self.largeur_ecran, self.hauteur_ecran),
                )
            else:
                # Effet de lumière du curseur seulement si la souris est sur la carte
                x, y = pygame.mouse.get_pos()
                if x < self.largeur_ecran:
                    # Portée de base du curseur
                    portee_curseur = 100
                    # Vérifier si le joueur a le sort de vision et augmenter la portée
                    if "vision" in self.sorts:
                        portee_curseur = self.sorts["vision"].portee
                    pygame.draw.circle(
                        nuit_surface, (0, 0, 0, 0), (x, y), portee_curseur
                    )  # dessin de la lumiere
            self.majFeuxDeCamps(dt, nuit_surface)

            ecran.blit(nuit_surface, (0, 0))
        else:
            self.majFeuxDeCamps(dt, None)
        
        self.shop_manager.dessiner_boutique_tours(ecran)
        self.shop_manager.dessiner_boutique_sorts(ecran)
        self.ennemi_manager.dessiner_ennemis(ecran)

        # Affichage des effets visuels des sorts
        for sort in self.sorts.values():
            sort.dessiner_effet(ecran, self)

        # Dessiner les projectiles et effets d'explosion
        self.tour_manager.dessiner_projectiles(ecran)
        self.tour_manager.dessiner_effets_explosion(ecran)

        # self.pointeur.draw(ecran, self)  # Désactivé pour enlever le filtre bleu
        self.maj(dt)

    def jouer_sfx(self, fichier: str, volume: float = 1.0) -> None:
        """Joue un son ponctuel depuis assets/audio/bruitage en respectant l'état muet."""
        try:
            if self.est_muet:
                return
            chemin = os.path.join(AUDIO_DIR, "bruitage", fichier)
            if not os.path.exists(chemin):
                return
            if fichier not in self._sons_cache:
                self._sons_cache[fichier] = pygame.mixer.Sound(chemin)
            son = self._sons_cache[fichier]
            son.set_volume(volume)
            son.play()
        except Exception:
            print("Erreur lors de la lecture du son ")
            # On ignore silencieusement les erreurs audio (pas de périphérique, etc.)
            pass

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
            if self._position_dans_grille(pos):
                self.case_survolee = self._case_depuis_pos(pos)
            else:
                self.case_survolee = None

        # Clic gauche: sélection dans la boutique et placement d'une tour
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            # Vérifier si l'éclair est sélectionné et cliquer sur une case
            if hasattr(self, "eclair_selectionne") and self.eclair_selectionne:
                if self._position_dans_grille(pos):
                    case = self._case_depuis_pos(pos)
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
            if self.bouton_vague.rect.collidepoint(pos) and self.vague_terminee():
                self.bouton_vague.action()
                self.tour_manager.tour_selectionnee = None  # désélectionne la range
                return None
            if self.shop_manager.gerer_clic_boutique_tours(pos):
                self.tour_manager.tour_selectionnee = None  # désélectionne la range
                return None

            # Placement de tour (priorité sur la sélection)
            if self.type_selectionne and self._position_dans_grille(pos):
                case = self._case_depuis_pos(pos)
                if case and self.tour_manager.peut_placer_tour(case, self.type_selectionne, self.cases_bannies):
                    if self.tour_manager.placer_tour(case, self.type_selectionne):
                        self.type_selectionne = None
                        self.tour_manager.tour_selectionnee = None  # désélectionne la range
                return None
            
            # --- Ajout : sélection/désélection d'une tour placée pour afficher la range ---
            if self._position_dans_grille(pos):
                case = self._case_depuis_pos(pos)
                self.tour_manager.selectionner_tour(case)
                return None

        # Clic droit: vendre une tour posée (si on clique sur une case occupée)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            pos = event.pos
            # On ignore si on clique dans la zone boutique
            if self.shop_manager.rect_boutique.collidepoint(pos):
                self.tour_manager.tour_selectionnee = None  # désélectionne la range
                return None
            if self._position_dans_grille(pos):
                case = self._case_depuis_pos(pos)
                if case and case in self.tour_manager.positions_occupees:
                    self.tour_manager.vendre_tour(case)
                    self.tour_manager.tour_selectionnee = None  # désélectionne la range

        return None

    # ---------- Vagues ----------
    def lancerVague(self):
        """Démarre une nouvelle vague d'ennemis, chargée depuis un CSV."""
        self.ennemi_manager.lancer_vague()

    def majvague(self):
        """Fait apparaître les ennemis au moment de leur temps d'apparition."""
        self.ennemi_manager.mettre_a_jour_vague()

    # ---------- Chemin / placement ----------
    def _cases_depuis_chemin(
        self, chemin_positions: list[Position]
    ) -> set[tuple[int, int]]:
        """Approxime les cases de grille traversées par le polygone du chemin."""
        bannies: set[tuple[int, int]] = set()
        if not chemin_positions:
            return bannies

        # Ajoute les cases des points eux-mêmes
        for p in chemin_positions:
            x_case = int(p.x) // self.taille_case
            y_case = int(p.y) // self.taille_case
            if 0 <= x_case < self.colonnes and 0 <= y_case < self.lignes:
                bannies.add((x_case, y_case))

        # Echantillonne les segments
        for i in range(len(chemin_positions) - 1):
            p0 = chemin_positions[i]
            p1 = chemin_positions[i + 1]
            dx = p1.x - p0.x
            dy = p1.y - p0.y
            dist = max(1.0, (dx * dx + dy * dy) ** 0.5)
            pas = max(1, int(dist / (self.taille_case / 4)))  # échantillonnage fin
            for s in range(pas + 1):
                t = s / pas
                x = p0.x + dx * t
                y = p0.y + dy * t
                x_case = int(x) // self.taille_case
                y_case = int(y) // self.taille_case
                if 0 <= x_case < self.colonnes and 0 <= y_case < self.lignes:
                    bannies.add((x_case, y_case))

        return bannies

    def vague_terminee(self) -> bool:
        """Retourne True si tous les ennemis sont morts ou arrivés au bout."""
        return self.ennemi_manager.vague_terminee()

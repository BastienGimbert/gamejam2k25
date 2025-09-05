from __future__ import annotations

import os
import pygame
import math

from classes.pointeur import Pointeur
from classes.ennemi import Gobelin, Mage, Ennemi 
from classes.joueur import Joueur
from classes.position import Position
from classes.tour import Archer, Catapult, FeuDeCamps, Tour
from classes.tour import Mage as TourMage
from classes.projectile import ProjectileFleche, ProjectileMageEnnemi, ProjectilePierre, ProjectileTourMage
from classes.utils import charger_chemin_tiled, decouper_sprite, distance_positions
from classes.csv import creer_liste_ennemis_depuis_csv
from classes.bouton import Bouton
from classes.sort import SortVision, SortFee, SortEclair

from classes.constants import ASSETS_DIR, PROJECT_ROOT, MONEY_DIR, HEART_DIR, TOWER_DIR, \
    COIN_ANIM_INTERVAL_MS, HEART_ANIM_INTERVAL_MS, MAP_PNG, DEFAULT_TOWER_TYPES, MAP_TILESET_TMJ, SPELLS_HEIGHT, GAME_HEIGHT, SHOP_WIDTH, TILE_SIZE, GRID_COLS, GRID_ROWS, GAME_WIDTH, WINDOW_HEIGHT


class Game:
    def __init__(self, police: pygame.font.Font, est_muet: bool = False):
        self.joueur = Joueur(argent=35, point_de_vie=100, sort="feu", etat="normal")
        self.police = police
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

        # Boutique (à droite de la carte)
        self.largeur_boutique = SHOP_WIDTH
        self.rect_boutique = pygame.Rect(self.largeur_ecran, 0, self.largeur_boutique, self.hauteur_ecran)
        
        # Boutique de sorts (en bas de l'écran)
        self.hauteur_boutique_sorts = SPELLS_HEIGHT
        self.rect_boutique_sorts = pygame.Rect(0, self.hauteur_ecran, WINDOW_HEIGHT, self.hauteur_boutique_sorts)
        
        # Sorts du joueur
        self.sorts = {
            "vision": SortVision(niveau=1),
            "fee": SortFee(niveau=1),
            "eclair": SortEclair(niveau=1)
        }
        
        # État de sélection des sorts
        self.eclair_selectionne = False
        # Prix par type de tour (affichage et logique d'achat/vente)
        self.prix_par_type: dict[str, int] = {
            "archer": getattr(Archer, "PRIX"),
            "catapult": getattr(Catapult, "PRIX"),
            "mage": getattr(TourMage, "PRIX"),
            "Feu de camp": getattr(FeuDeCamps, "PRIX"),
        }

        self.portee_par_type: dict[str, float] = {
            "archer": getattr(Archer, "PORTEE"),
            "catapult": getattr(Catapult, "PORTEE"),
            "mage": getattr(TourMage, "PORTEE"),
            "Feu de camp": getattr(FeuDeCamps, "PORTEE"),
        }


        # Animation monnaie
        self.coin_frames = self._charger_piece()
        self.coin_frame_idx = 0
        self.COIN_ANIM_INTERVAL = COIN_ANIM_INTERVAL_MS
        self.last_coin_ticks = pygame.time.get_ticks()

        # Animation coeurs (PV)
        self.heart_frames = self._charger_coeurs()
        self.heart_frame_idx = 0
        self.HEART_ANIM_INTERVAL = HEART_ANIM_INTERVAL_MS
        self.last_heart_ticks = pygame.time.get_ticks()

        # Types de tours
        self.tower_types = DEFAULT_TOWER_TYPES
        # --- Ajout : sélection de tour pour affichage de la range ---
        self.tour_selectionnee: tuple[int, int] | None = None
        
        self.tower_assets = self._charger_tours()
        self.shop_items = self._creer_boutons_boutique()
        self.type_selectionne: str | None = None

        # Occupation des cases (affichage)
        self.positions_occupees: dict[tuple[int, int], dict] = {}

        # Tours / projectiles (logique)
        self.tours: list[Tour] = []
        self.projectiles: list[ProjectileFleche | ProjectilePierre | ProjectileTourMage] = []


        # Couleurs UI
        # Projectiles actifs (flèches, etc.)
        # Peut contenir ProjectileFleche et ProjectilePierre
        self.projectiles: list = []
        # Images de base des projectiles (chargées via une fonction générique)
        self.image_fleche = self._charger_image_projectile(ProjectileFleche.CHEMIN_IMAGE)
        self.image_pierre = self._charger_image_projectile(ProjectilePierre.CHEMIN_IMAGE)
        # Projectile de la tour mage
        self.image_orbe_mage = self._charger_image_projectile(ProjectileTourMage.CHEMIN_IMAGE)
        self.image_projectileMageEnnemi = self._charger_image_projectile(ProjectileMageEnnemi.CHEMIN_IMAGE)


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
        medieval_couleurs = {
            "fond_normal": (110, 70, 30),      # brun
            "fond_survol": (150, 100, 40),    # brun clair
            "contour": (220, 180, 60),        # doré
            "texte": (240, 220, 180),         # beige
        }
        police_medievale = pygame.font.Font(None, 38)  # police plus grande, à adapter si tu as une police médiévale
        self.bouton_vague = Bouton(
            "Lancer la vague",
            self.rect_boutique.x + 20,
            self.hauteur_ecran - 70,
            self.largeur_boutique - 40,
            50,
            self.lancerVague,
            police_medievale,
            medieval_couleurs
        )

        # Gestion des vagues
        self.numVague = 0
        self.debutVague = 0
        self.ennemis: list[Ennemi] = []  # Rempli lors du lancement de vague
        
        #self.action_bouton= self.lancerVague()            
        #self.bouton = Bouton("Bouton", 100, 100, 200, 50, self.action_bouton, self.police, self.couleurs)

    def getToursFeuDeCamp(self) -> list[FeuDeCamps]:
        return [t for t in self.tours if isinstance(t, FeuDeCamps)]

    def dansFeuDeCamp(self, position: Position) -> bool:
        for t in self.getToursFeuDeCamp():
            if distance_positions(t.position, position) <= t.portee:
                return True
        return False

    def _ennemi_atteint_chateau(self, ennemi: Ennemi) -> None:
        # Inflige les dégâts de l'ennemi au joueur lorsque l'ennemi atteint la fin
        try:
            deg = getattr(ennemi, "degats", 1)
        except Exception:
            deg = 1
        self.joueur.point_de_vie = max(0, int(self.joueur.point_de_vie) - int(deg))
        # Le marquer comme "mort" pour que les tours cessent de le cibler
        try:
            ennemi.pointsDeVie = 0
        except Exception:
            pass

    # ---------- Chargements ----------
    def _charger_carte(self):
        chemin_carte = MAP_PNG
        if not os.path.exists(chemin_carte):
            raise FileNotFoundError(f"Carte non trouvée: {chemin_carte}")
        img = pygame.image.load(chemin_carte).convert_alpha()
        return img

    def _charger_piece(self):
        coinImg = os.path.join(MONEY_DIR, "MonedaD.png")
        if os.path.exists(coinImg):
            img = pygame.image.load(coinImg).convert_alpha()
            frames = decouper_sprite(img, 5, horizontal=True, copy=True)
            frames = [pygame.transform.smoothscale(f, (24, 24)) for f in frames]
            return frames
        return []

    def _charger_coeurs(self):
        """Charge toutes les images de coeur dans assets/heart et retourne une liste de surfaces."""
        frames = []
        if not os.path.isdir(HEART_DIR):
            return frames
        fichiers = [f for f in os.listdir(HEART_DIR) if f.lower().endswith(".png")]
        if not fichiers:
            return frames
        fichiers.sort()
        for fn in fichiers:
            p = os.path.join(HEART_DIR, fn)
            try:
                img = pygame.image.load(p).convert_alpha()
                frames.append(img)
            except Exception:
                continue
        return frames

    def _charger_tours(self):
        assets = {}
        for tower_type in self.tower_types:
            tower_folder = os.path.join(TOWER_DIR, tower_type)
            if not os.path.isdir(tower_folder):
                continue

            chemins = [f for f in os.listdir(tower_folder) if f.endswith(".png")]
            if not chemins:
                continue

            chemins.sort()

            # feu de camp : 6 images 
            if tower_type == "Feu de camp":
                dernier_chemin = os.path.join(tower_folder, chemins[-1])
                image = pygame.image.load(dernier_chemin).convert_alpha()
                slices = decouper_sprite(image, 6, horizontal=True, copy=False)  
                frames = [slices]
                assets[tower_type] = {
                    "frames": frames,
                    "icon": pygame.transform.smoothscale(slices[0], (48, 48)) 
                }
            else:
                # Cas tour classique : découpe en 4
                dernier_chemin = os.path.join(tower_folder, chemins[-1])
                image = pygame.image.load(dernier_chemin).convert_alpha()
                slices = decouper_sprite(image, 4, horizontal=True, copy=False)
                frames = [slices]
                icon = pygame.transform.smoothscale(slices[2], (48, 48))
                assets[tower_type] = {"frames": frames, "icon": icon}

        return assets


    def _creer_boutons_boutique(self):
        boutons = []
        x = self.rect_boutique.x + 20
        y = 100
        espace_y = 90
        for t in self.tower_types:
            rect = pygame.Rect(x, y, self.largeur_boutique - 40, 70)
            boutons.append({"type": t, "rect": rect})
            y += espace_y
        return boutons

    def _charger_image_projectile(self, chemin_relatif: str):
        if not chemin_relatif:
            # Fallback simple
            surf = pygame.Surface((22, 22), pygame.SRCALPHA)
            pygame.draw.circle(surf, (120, 120, 120), (11, 11), 10)
            return surf

        p = os.path.join(PROJECT_ROOT, chemin_relatif)
        if os.path.exists(p):
            try:
                return pygame.image.load(p).convert_alpha()
            except Exception:
                pass
        # Fallbacks
        if "archer" in chemin_relatif:
            surf = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.line(surf, (220, 220, 50), (12, 2), (12, 22), 3)
            return surf
        surf = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(surf, (120, 120, 120), (11, 11), 10)
        return surf

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
            pygame.draw.line(ecran, self.couleur_quadrillage, (x, 0), (x, self.hauteur_ecran))
        for y in range(0, self.hauteur_ecran + 1, self.taille_case):
            pygame.draw.line(ecran, self.couleur_quadrillage, (0, y), (largeur_draw, y))

    def _dessiner_personnages_tours(self, ecran):
        for t in self.tours:
            t.draw_person(ecran)


    def _dessiner_boutique(self, ecran):
        pygame.draw.rect(ecran, self.couleur_boutique_bg, self.rect_boutique)
        pygame.draw.rect(ecran, self.couleur_boutique_border, self.rect_boutique, 2)
        titre = self.police.render("Boutique", True, self.couleur_texte)
        ecran.blit(titre, (self.rect_boutique.x + (self.largeur_boutique - titre.get_width()) // 2, 20))

        # Monnaie
        if self.coin_frames:
            coin = self.coin_frames[self.coin_frame_idx % len(self.coin_frames)]
            ecran.blit(coin, (self.rect_boutique.x + 20, 60))
            now = pygame.time.get_ticks()
            if now - self.last_coin_ticks >= self.COIN_ANIM_INTERVAL:
                self.coin_frame_idx = (self.coin_frame_idx + 1) % len(self.coin_frames)
                self.last_coin_ticks = now
        txt_solde = self.police.render(f"{self.joueur.argent}", True, self.couleur_texte)
        # Décale le texte si l'argent est grand
        ecran.blit(txt_solde, (self.rect_boutique.x + 50, 56))
    

        # Points de vie
        coeur_pos = (self.rect_boutique.x + 140, 60)
        if self.heart_frames:
            coeur = self.heart_frames[self.heart_frame_idx % len(self.heart_frames)]
            coeur_s = pygame.transform.smoothscale(coeur, (24, 24))
            ecran.blit(coeur_s, coeur_pos)
            now = pygame.time.get_ticks()
            if now - self.last_heart_ticks >= self.HEART_ANIM_INTERVAL:
                self.heart_frame_idx = (self.heart_frame_idx + 1) % len(self.heart_frames)
                self.last_heart_ticks = now
        else:
            # Petit fallback visuel si aucun asset
            pygame.draw.circle(ecran, (220, 50, 50), (coeur_pos[0] + 12, coeur_pos[1] + 12), 12)
        txt_pv = self.police.render(f"{self.joueur.point_de_vie}", True, self.couleur_texte)
        ecran.blit(txt_pv, (coeur_pos[0] + 30, coeur_pos[1]))

        # Boutons tours
        for item in self.shop_items:
            rect = item["rect"]
            t = item["type"]
            hover = rect.collidepoint(pygame.mouse.get_pos())
            # --- Ajout : fond hover si sélectionné ---
            if self.type_selectionne == t or hover:
                couleur_fond_boutton = self.couleur_bouton_hover
            else:
                couleur_fond_boutton = self.couleur_bouton_bg
            pygame.draw.rect(
                ecran,
                couleur_fond_boutton,
                rect,
                border_radius=6,
            )
            pygame.draw.rect(ecran, self.couleur_boutique_border, rect, 2, border_radius=6)

            # label centré verticalement
            label = self.police.render(t.capitalize(), True, self.couleur_texte)


            label_y = rect.y + (rect.h - label.get_height()) // 2

            # icône (si disponible) centrée verticalement
            icon = None

            if t in self.tower_assets:
                icon = self.tower_assets[t].get("icon")
            if icon:
                icon_y = rect.y + (rect.h - icon.get_height()) // 2
                ecran.blit(icon, (rect.x + 10, icon_y))

            # position du label (après icône)
            label_x = rect.x + 70
            ecran.blit(label, (label_x, label_y))

            # prix : aligné à droite et centré verticalement, couleur selon solvabilité
            prix_val = self.prix_par_type.get(t, 0)
            can_buy = self.joueur.argent >= prix_val
            prix_color = (240, 240, 240) if can_buy else (220, 80, 80)
            prix = self.police.render(f"{prix_val}", True, prix_color)

            # icône de pièce : utilise frames chargées si disponibles, sinon fallback circulaire
            coin_w, coin_h = 20, 20
            if self.coin_frames:
                coin_frame = self.coin_frames[self.coin_frame_idx % len(self.coin_frames)]
                try:
                    coin_surf = pygame.transform.smoothscale(coin_frame, (coin_w, coin_h))
                except Exception:
                    coin_surf = coin_frame
            else:
                coin_surf = pygame.Surface((coin_w, coin_h), pygame.SRCALPHA)
                pygame.draw.circle(coin_surf, (220, 200, 40), (coin_w // 2, coin_h // 2), coin_w // 2)

            # aligne coin au bord droit du bouton, prix à sa gauche
            gap = 6
            coin_x = rect.right - 10 - coin_surf.get_width()
            prix_x = coin_x - gap - prix.get_width()

            # centrage vertical
            prix_y = rect.y + (rect.h - prix.get_height()) // 2
            coin_y = rect.y + (rect.h - coin_surf.get_height()) // 2

            # dessin: prix puis icône (icône à droite)
            ecran.blit(prix, (prix_x, prix_y))
            if coin_surf:
                ecran.blit(coin_surf, (coin_x, coin_y))

        bouton_actif = self.vague_terminee()

        # Affiche le numéro de vague au-dessus du bouton
        try:
            label_vague = self.police.render(f"Vague n° {self.numVague}", True, self.couleur_texte)
            label_x = self.bouton_vague.rect.x + (self.bouton_vague.rect.w - label_vague.get_width()) // 2
            label_y = self.bouton_vague.rect.y - 36
            ecran.blit(label_vague, (label_x, label_y))
        except Exception:
            pass

        if bouton_actif:
            self.bouton_vague.dessiner(ecran)
        else:
            # Dessin grisé
            old_couleurs = self.bouton_vague.couleurs.copy()
            self.bouton_vague.couleurs["fond_normal"] = (120, 120, 120)
            self.bouton_vague.couleurs["fond_survol"] = (160, 160, 160)
            self.bouton_vague.couleurs["texte"] = (180, 180, 180)
            self.bouton_vague.dessiner(ecran)
            self.bouton_vague.couleurs = old_couleurs

    def _dessiner_boutique_sorts(self, ecran):
        """Dessine la boutique de sorts en bas de l'écran."""
        pygame.draw.rect(ecran, self.couleur_boutique_sorts_bg, self.rect_boutique_sorts)
        pygame.draw.rect(ecran, self.couleur_boutique_sorts_border, self.rect_boutique_sorts, 2)
        
        # Titre de la boutique de sorts
        titre = self.police.render("Boutique de sorts", True, self.couleur_texte)
        ecran.blit(titre, (self.rect_boutique_sorts.x + (self.rect_boutique_sorts.width - titre.get_width()) // 2, 
                          self.rect_boutique_sorts.y + 20))
        
        # Affichage des sorts disponibles
        y_offset = 60
        x_offset = 20
        
        for sort_key, sort in self.sorts.items():
            # Rectangle pour le sort (même style que la boutique)
            sort_rect = pygame.Rect(
                self.rect_boutique_sorts.x + x_offset,
                self.rect_boutique_sorts.y + y_offset,
                300,
                80
            )
            
            # Vérifier si le sort est au niveau maximum
            is_max_level = hasattr(sort, 'est_au_niveau_maximum') and sort.est_au_niveau_maximum()
            
            # Pour le sort de la fée, vérifier s'il est déjà actif
            is_fee_active = sort_key == "fee" and hasattr(sort, 'est_actif') and sort.est_actif()
            
            # Pour l'éclair, vérifier s'il est sélectionné
            is_eclair_selected = sort_key == "eclair" and hasattr(self, 'eclair_selectionne') and self.eclair_selectionne
            
            # Effet de survol (comme dans la boutique)
            hover = sort_rect.collidepoint(pygame.mouse.get_pos())
            can_buy = sort.peut_etre_achete(self.joueur.argent) and not is_max_level and not is_fee_active and not is_eclair_selected
            
            if hover and can_buy:
                couleur_fond = self.couleur_bouton_hover
            else:
                couleur_fond = self.couleur_bouton_bg
            
            # Dessin avec bordures arrondies (comme la boutique)
            pygame.draw.rect(ecran, couleur_fond, sort_rect, border_radius=6)
            pygame.draw.rect(ecran, self.couleur_boutique_sorts_border, sort_rect, 2, border_radius=6)
            
            # Nom du sort avec niveau (style boutique)
            if is_max_level or is_fee_active or is_eclair_selected:
                # Grisé quand au niveau maximum, quand la fée est active, ou quand l'éclair est sélectionné
                nom_sort = self.police.render(sort.nom_complet, True, (120, 120, 120))
            else:
                nom_sort = self.police.render(sort.nom_complet, True, self.couleur_texte)
            ecran.blit(nom_sort, (sort_rect.x + 10, sort_rect.y + 10))
            
            # Prix et icône seulement si pas au niveau maximum, pas actif, et pas sélectionné
            if not is_max_level and not is_fee_active and not is_eclair_selected:
                # Prix avec couleur selon solvabilité (comme la boutique)
                prix_color = self.couleur_texte if can_buy else (220, 80, 80)
                prix_text = self.police.render(f"{sort.prix}", True, prix_color)
                
                # Icône de pièce (comme la boutique)
                coin_w, coin_h = 20, 20
                if self.coin_frames:
                    coin_frame = self.coin_frames[self.coin_frame_idx % len(self.coin_frames)]
                    try:
                        coin_surf = pygame.transform.smoothscale(coin_frame, (coin_w, coin_h))
                    except Exception:
                        coin_surf = coin_frame
                else:
                    coin_surf = pygame.Surface((coin_w, coin_h), pygame.SRCALPHA)
                    pygame.draw.circle(coin_surf, (220, 200, 40), (coin_w // 2, coin_h // 2), coin_w // 2)
                
                # Positionnement du prix et de l'icône (comme la boutique)
                gap = 6
                coin_x = sort_rect.right - 10 - coin_surf.get_width()
                prix_x = coin_x - gap - prix_text.get_width()
                prix_y = sort_rect.y + 40
                coin_y = sort_rect.y + 40
                
                ecran.blit(prix_text, (prix_x, prix_y))
                if coin_surf:
                    ecran.blit(coin_surf, (coin_x, coin_y))
            elif is_max_level:
                # Afficher "MAX" à la place du prix
                max_text = self.police.render("MAX", True, (100, 200, 100))
                max_x = sort_rect.right - 10 - max_text.get_width()
                max_y = sort_rect.y + 40
                ecran.blit(max_text, (max_x, max_y))
            elif is_fee_active:
                # Afficher "ACTIF" pour la fée
                actif_text = self.police.render("ACTIF", True, (100, 200, 100))
                actif_x = sort_rect.right - 10 - actif_text.get_width()
                actif_y = sort_rect.y + 40
                ecran.blit(actif_text, (actif_x, actif_y))
            elif is_eclair_selected:
                # Afficher "SÉLECTIONNÉ" pour l'éclair
                selected_text = self.police.render("SÉLECTIONNÉ", True, (255, 200, 0))
                selected_x = sort_rect.right - 10 - selected_text.get_width()
                selected_y = sort_rect.y + 40
                ecran.blit(selected_text, (selected_x, selected_y))
            
            # Pas d'affichage de portée pour garder l'interface propre
            
            x_offset += 320  # Espacement entre les sorts

    def _dessiner_surbrillance(self, ecran):
        # Surbrillance pour l'éclair (seulement sur les cases du chemin, sauf les 6 en haut à gauche)
        if hasattr(self, 'eclair_selectionne') and self.eclair_selectionne and self.case_survolee:
            if (self.case_survolee in getattr(self, "cases_bannies", set()) and 
                self.case_survolee not in [(x, y) for y in (0, 1) for x in range(0, 6)]):
                x_case, y_case = self.case_survolee
                rect = pygame.Rect(x_case * self.taille_case, y_case * self.taille_case, self.taille_case, self.taille_case)
                overlay = pygame.Surface((self.taille_case, self.taille_case), pygame.SRCALPHA)
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
            self.taille_case
        )

        #Surbrillance
        overlay = pygame.Surface((self.taille_case, self.taille_case), pygame.SRCALPHA)
        interdit = (
            (x_case, y_case) in getattr(self, "cases_bannies", set())
            or (x_case, y_case) in self.positions_occupees
        )
        couleur = self.couleur_surbrillance_interdite if interdit else self.couleur_surbrillance
        overlay.fill((*couleur, 80))
        if rect.right <= self.largeur_ecran:
            ecran.blit(overlay, rect)

        # Cercle autour de la case

        portee = self.portee_par_type.get(self.type_selectionne, 0)
        cx = x_case * self.taille_case + self.taille_case // 2
        cy = y_case * self.taille_case + self.taille_case // 2

        # Dessine un cercle
        dash_count = 15     # nombre de segments
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
        """Dessine les tours, avec un traitement spécial pour FeuDeCamps."""
        for (x_case, y_case), data in self.positions_occupees.items():
            tour = data.get("instance")

            if tour and hasattr(tour, "dessiner"):
                # FeuDeCamps (et éventuellement d'autres tours spéciales)
                tour.dessiner(ecran, self.taille_case)
            else:
                # Cas standard (anciennes tours fixes)
                ttype = data["type"]
                surf = None
                if ttype in self.tower_assets and self.tower_assets[ttype]["frames"]:
                    slices = self.tower_assets[ttype]["frames"][0]
                    surf = slices[2]
                    surf = pygame.transform.smoothscale(surf, (self.taille_case, self.taille_case))
                if surf is None:
                    surf = pygame.Surface((self.taille_case, self.taille_case))
                    surf.fill((150, 150, 180))
                ecran.blit(surf, (x_case * self.taille_case, y_case * self.taille_case))


            # --- Ajout : affichage range si sélectionnée ---
            if self.tour_selectionnee == (x_case, y_case):

                # Cherche la tour correspondante
                tour = None
                cx = x_case * self.taille_case + self.taille_case // 2
                cy = y_case * self.taille_case + self.taille_case // 2
                for t in self.tours:
                    if int(t.position.x) == cx and int(t.position.y) == cy:
                        tour = t
                        break

                if tour and hasattr(tour, "portee"):
                    portee = getattr(tour, "portee", 120)

                    # Dessine un cercle
                    dash_count = 15     # nombre de segments
                    dash_length = 0.15  # en radians

                    for i in range(dash_count):
                        angle_start = 2 * math.pi * i / dash_count
                        angle_end = angle_start + dash_length
                        x1 = int(cx + portee * math.cos(angle_start))
                        y1 = int(cy + portee * math.sin(angle_start))
                        x2 = int(cx + portee * math.cos(angle_end))
                        y2 = int(cy + portee * math.sin(angle_end))
                        pygame.draw.line(ecran, (255, 255, 255), (x1, y1), (x2, y2), 3)

    def dessiner_ennemis(self, ecran):
        for e in self.ennemis:
            # Compat : certains ennemis peuvent avoir des états (apparu/mort/arrivé)
            try:
                doit_dessiner = (
                    (not hasattr(e, "estApparu") or e.estApparu(self.debutVague))
                    and (not hasattr(e, "estMort") or not e.estMort())
                    and (not hasattr(e, "a_atteint_le_bout") or not e.a_atteint_le_bout())
                )
            except Exception:
                doit_dessiner = True
            if doit_dessiner:
                if hasattr(e, "majVisible"):
                    e.majVisible(self)
                if hasattr(e, "draw"):
                    e.draw(ecran)
                # --- Barre de PV ---
                if hasattr(e, "pointsDeVie") and hasattr(e, "pointsDeVieMax") and e.pointsDeVie < e.pointsDeVieMax:
                    # Position de la barre : juste au-dessus de l'ennemi
                    px = int(e.position.x)
                    py = int(e.position.y)

                    largeur_max = 40
                    hauteur = 4

                    ratio = max(0, min(1, e.pointsDeVie / e.pointsDeVieMax))
                    largeur_barre = int(largeur_max * ratio)

                    x_barre = px - largeur_max // 2
                    y_barre = py - 40  # Espace entre le haut du sprite et l'ennemi

                    # Fond gris
                    pygame.draw.rect(ecran, (60, 60, 60), (x_barre, y_barre, largeur_max, hauteur), border_radius=3)

                    # Barre rouge
                    pygame.draw.rect(ecran, (220, 50, 50), (x_barre, y_barre, largeur_barre, hauteur), border_radius=3)

    # ---------- Update / boucle ----------
    def maj(self, dt: float):
        # Apparition des ennemis selon la vague
        self.majvague()

        # Déplacement des ennemis actifs
        for e in self.ennemis:
            try:
                if not hasattr(e, "estApparu") or e.estApparu(self.debutVague):
                    e.seDeplacer(dt)
                    e.update_animation(dt)
            except Exception:
                if hasattr(e, "seDeplacer"):
                    e.seDeplacer(dt)
        
        # Appliquer les effets des sorts
        for sort in self.sorts.values():
            sort.appliquer_effet(self)

        # Perte de PV si un ennemi touche certaines cases "château"
        for e in self.ennemis:
            try:
                pos_px = (int(e.position.x), int(e.position.y))
                case = self._case_depuis_pos(pos_px)
                if case in {(2, 0), (3, 0)}:
                    deg = getattr(e, "degats", 1)
                    self.joueur.point_de_vie = max(0, int(self.joueur.point_de_vie) - int(deg))
                    try:
                        setattr(e, "_ne_pas_recompenser", True)
                    except Exception:
                        pass
                    if hasattr(e, "perdreVie"):
                        e.perdreVie(getattr(e, "pointsDeVie", 1))
                    else:
                        try:
                            e.pointsDeVie = 0
                        except Exception:
                            pass
            except Exception:
                continue

        # Mise à jour des tours (acquisition cible + tir)
        for t in self.tours:

            if isinstance(t, FeuDeCamps):
                continue 
            def au_tir(tour: Tour, cible: Gobelin):
                if isinstance(tour, Archer) and self.image_fleche is not None:
                    p = ProjectileFleche(origine=tour.position, cible_pos=cible.position.copy())
                    p.cible = cible              # suivi de la cible (comme une flèche)
                    p.image_base = self.image_fleche
                    self.projectiles.append(p)
                    # Joue le son de flèche
                    try:
                        arrow_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "audio", "bruitage", "arrow.mp3"))
                        arrow_sound.play().set_volume(0.15)
                    except Exception:
                        pass

                elif isinstance(tour, Catapult) and self.image_pierre is not None:
                    p = ProjectilePierre(origine=tour.position, cible_pos=cible.position.copy(), game_ref=self)
                    p.cible = cible
                    p.image_base = self.image_pierre
                    self.projectiles.append(p)
                    # Joue le son de catapulte
                    try:
                        fire_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "audio", "bruitage", "fire-magic.mp3"))
                        fire_sound.play().set_volume(0.15)
                    except Exception:
                        pass
                    # Déclenche la réaction du mage le plus proche pour intercepter la pierre
                    mage = self.get_closest_mage(p.position)
                    if mage is None:
                        # Fallback: mage le plus proche non mort, même si cooldown pas prêt
                        try:
                            candidats = [e for e in self.ennemis if isinstance(e, Mage) and not e.estMort() and e.estApparu(self.debutVague)]
                            if candidats:
                                mage = min(candidats, key=lambda m: distance_positions(m.position, p.position))
                        except Exception:
                            mage = None
                    if mage is not None and getattr(self, "image_projectileMageEnnemi", None) is not None:
                        mage.react_to_projectile()
                        pm = ProjectileMageEnnemi(origine=mage.position.copy(), cible_proj=p, vitesse=700.0)
                        pm.image_base = self.image_projectileMageEnnemi
                        self.projectiles.append(pm)

                elif isinstance(tour, TourMage) and self.image_orbe_mage is not None:
                    # LOGIQUE SIMPLE identique à l'archer (pas d'interception ici)
                    p = ProjectileTourMage(origine=tour.position, cible_pos=cible.position.copy())
                    p.cible = cible
                    p.image_base = self.image_orbe_mage
                    self.projectiles.append(p)
                    # Joue le son du mage
                    try:
                        wind_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "audio", "bruitage", "wind-magic.mp3"))
                        wind_sound.play().set_volume(0.15)
                    except Exception:
                        pass

            if hasattr(t, "maj"):
                t.maj(dt, self.ennemis, au_tir=au_tir)

        # Mise à jour des projectiles + collisions
        for pr in self.projectiles:
            if hasattr(pr, "mettreAJour"):
                pr.mettreAJour(dt)
            if getattr(pr, "detruit", False):
                continue

            if not isinstance(pr, ProjectileMageEnnemi):
                # Collision projectiles tours -> ennemis
                for e in self.ennemis:
                    if hasattr(e, "estMort") and e.estMort():
                        continue
                    if hasattr(pr, "aTouche") and pr.aTouche(e):
                        if hasattr(pr, "appliquerDegats"):
                            pr.appliquerDegats(e)
                            try:
                                if e.estMort() and not getattr(e, "_recompense_donnee", False) and not getattr(e, "_ne_pas_recompenser", False):
                                    self.joueur.argent += int(getattr(e, "argent", 0))
                                    setattr(e, "_recompense_donnee", True)
                            except Exception:
                                pass
                        break
            else:
                # Collision spécifique projectile mage ennemi -> projectile de catapulte (si encore utilisé)
                cible = getattr(pr, "cible_proj", None)
                if cible and hasattr(pr, "aTouche") and pr.aTouche(cible):
                    cible.detruit = True
                    pr.detruit = True

        # Nettoyage projectiles
        self.projectiles = [p for p in self.projectiles if not getattr(p, "detruit", False)]

        # Nettoyage ennemis
        self.ennemis = [
            e for e in self.ennemis
            if not (
                getattr(e, "estMort", lambda: False)() or
                getattr(e, "a_atteint_le_bout", lambda: False)()
            )
        ]
        
    def get_closest_mage(self, pos: Position) -> None | Mage:
        """Retourne le mage le plus proche de la position pos."""
        mages = [e for e in self.ennemis if isinstance(e, Mage) and not e.estMort() and e.estApparu(self.debutVague) and e.ready_to_attack()]
        if not mages:
            return None
        nearestMage = mages[0]
        distance = distance_positions(nearestMage.position, pos)
        for m in mages :
            if distance_positions(m.position, pos) < distance:
                nearestMage = m
                distance = distance_positions(m.position, pos)
        
        return nearestMage
    
    def majFeuxDeCamps(self, dt: float, nuit_surface: pygame.Surface) -> None:
        """Met à jour et dessine les effets de lumière des feux de camps."""
        feux_de_camps = [t for t in self.tours if t.__class__.__name__ == "FeuDeCamps"]
        for feu in feux_de_camps:
            feu.maj(dt)
            radius = feu.portee
            pygame.draw.circle(nuit_surface, (0, 0, 0, 0), (feu.position.x, feu.position.y), radius)

    def dessiner(self, ecran: pygame.Surface) -> None:
        dt = self.clock.tick(60) / 1000.0
        ecran.blit(self.carte, (0, 0))
        self._dessiner_tours_placees(ecran)
        self._dessiner_personnages_tours(ecran)
        self._dessiner_surbrillance(ecran)
        
        # Effet nuit
        nuit_surface = pygame.Surface((self.largeur_ecran, self.hauteur_ecran), pygame.SRCALPHA)
        nuit_surface.fill((0, 6, 25, int(255 * 0.6)))  # 60% opacity

        # Vérifier si la fée est active
        if 'fee' in self.sorts and self.sorts['fee'].est_actif():
            # Si la fée est active, éclairer toute la carte
            pygame.draw.circle(nuit_surface, (0, 0, 0, 0), (self.largeur_ecran // 2, self.hauteur_ecran // 2), max(self.largeur_ecran, self.hauteur_ecran))
        else:
            # Effet de lumière du curseur seulement si la souris est sur la carte
            x, y = pygame.mouse.get_pos()
            if x < self.largeur_ecran: 
                # Portée de base du curseur
                portee_curseur = 100
                # Vérifier si le joueur a le sort de vision et augmenter la portée
                if 'vision' in self.sorts:
                    portee_curseur = self.sorts['vision'].portee
                pygame.draw.circle(nuit_surface, (0, 0, 0, 0), (x, y), portee_curseur) # dessin de la lumiere
        self.majFeuxDeCamps(dt, nuit_surface)

        ecran.blit(nuit_surface, (0, 0))


        self._dessiner_boutique(ecran) 
        self._dessiner_boutique_sorts(ecran)
        self.dessiner_ennemis(ecran)
        
        # Affichage des effets visuels des sorts
        for sort in self.sorts.values():
            sort.dessiner_effet(ecran, self)

        for pr in self.projectiles:
            if hasattr(pr, "dessiner"):
                pr.dessiner(ecran)

        # self.pointeur.draw(ecran, self)  # Désactivé pour enlever le filtre bleu
        self.maj(dt)

    def jouer_sfx(self, fichier: str, volume: float = 1.0) -> None:
        """Joue un son ponctuel depuis assets/audio/bruitage en respectant l'état muet."""
        try:
            if self.est_muet:
                return
            chemin = os.path.join(base_dir, "assets", "audio", "bruitage", fichier)
            if not os.path.exists(chemin):
                return
            if fichier not in self._sons_cache:
                self._sons_cache[fichier] = pygame.mixer.Sound(chemin)
            son = self._sons_cache[fichier]
            son.set_volume(volume)
            son.play()
        except Exception:
            # On ignore silencieusement les erreurs audio (pas de périphérique, etc.)
            pass
    
    def decompte_dt(self) -> None:
        dt = self.clock.tick(60) / 1000.0
    

    # ---------- Evénements ----------
    def gerer_evenement(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # Annuler la sélection d'éclair si elle est active
            if hasattr(self, 'eclair_selectionne') and self.eclair_selectionne:
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
            if hasattr(self, 'eclair_selectionne') and self.eclair_selectionne:
                if self._position_dans_grille(pos):
                    case = self._case_depuis_pos(pos)
                    if case and case in getattr(self, "cases_bannies", set()):
                        # L'éclair ne peut être utilisé que sur les cases du chemin
                        # Mais pas sur les 6 cases en haut à gauche (x=0..5, y=0..1)
                        x_case, y_case = case
                        if (x_case, y_case) in [(x, y) for y in (0, 1) for x in range(0, 6)]:
                            return None
                        # Activer l'éclair sur cette case
                        if self.sorts['eclair'].activer_sur_case(x_case, y_case):
                            # Son d'éclair (respecte muet)
                            self.jouer_sfx("loud-thunder.mp3")
                            # Débiter le prix
                            self.joueur.argent -= self.sorts['eclair'].prix
                            # Désélectionner l'éclair
                            self.eclair_selectionne = False
                        return None
            # Clic dans la boutique de sorts
            if self.rect_boutique_sorts.collidepoint(pos):
                x_offset = 20
                for sort_key, sort in self.sorts.items():
                    sort_rect = pygame.Rect(
                        self.rect_boutique_sorts.x + x_offset,
                        self.rect_boutique_sorts.y + 60,
                        300,
                        80
                    )
                    if sort_rect.collidepoint(pos):
                        # Vérifier si le sort n'est pas au niveau maximum
                        is_max_level = hasattr(sort, 'est_au_niveau_maximum') and sort.est_au_niveau_maximum()
                        # Vérifier si la fée n'est pas déjà active
                        is_fee_active = sort_key == "fee" and hasattr(sort, 'est_actif') and sort.est_actif()
                        
                        if sort_key == "eclair":
                            # Pour l'éclair, sélectionner le sort au lieu de l'acheter directement
                            if not is_max_level and sort.peut_etre_achete(self.joueur.argent):
                                self.eclair_selectionne = True
                                self.type_selectionne = None  # Désélectionner les tours
                        elif not is_max_level and not is_fee_active:
                            achat_ok = sort.acheter(self.joueur)
                            if achat_ok and sort_key == "fee":
                                # Son d'activation de la fée
                                self.jouer_sfx("magic-spell.mp3")
                        break
                    x_offset += 320
                return None
            # Clic dans la boutique
            if self.bouton_vague.rect.collidepoint(pos) and self.vague_terminee():
                self.bouton_vague.action()
                self.tour_selectionnee = None  # désélectionne la range
                return None
            if self.rect_boutique.collidepoint(pos):
                for item in self.shop_items:
                    if item["rect"].collidepoint(pos):
                        # Sélectionne le type uniquement si le joueur a assez d'argent
                        t = item["type"]
                        prix_t = self.prix_par_type.get(t, 0)

                        # Si déjà sélectionné, on désélectionne
                        if self.type_selectionne == t:
                            self.type_selectionne = None
                        elif self.joueur.argent >= prix_t:
                            self.type_selectionne = t
                        else:
                            self.type_selectionne = None
                        break
                self.tour_selectionnee = None  # désélectionne la range
                return None

            # --- Ajout : sélection/désélection d'une tour placée pour afficher la range ---
            if self._position_dans_grille(pos):
                case = self._case_depuis_pos(pos)
                if case and case in self.positions_occupees:
                    if self.tour_selectionnee == case:
                        self.tour_selectionnee = None  # désélectionne si déjà sélectionnée
                    else:
                        self.tour_selectionnee = case  # sélectionne la tour
                    return None
                else:
                    self.tour_selectionnee = None  # désélectionne si on clique ailleurs

            # Placement de tour
            if self.type_selectionne and self._position_dans_grille(pos):
                case = self._case_depuis_pos(pos)
                if (
                    case
                    and case not in self.positions_occupees
                    and self.joueur.argent >= self.prix_par_type.get(self.type_selectionne, 0)
                    and case not in getattr(self, "cases_bannies", set())
                ):
                    # 1) Marque la case occupée (affichage)
                    self.positions_occupees[case] = {"type": self.type_selectionne, "frame": 0}

                    # 2) Crée l'instance de tour (logique)
                    x_case, y_case = case
                    cx = x_case * self.taille_case + self.taille_case // 2
                    cy = y_case * self.taille_case + self.taille_case // 2
                    pos_tour = Position(cx, cy)
                    tour_id = len(self.tours) + 1
                    nouvelle_tour = None
                    if self.type_selectionne == "archer":
                        nouvelle_tour = Archer(id=tour_id, position=pos_tour)
                    elif self.type_selectionne == "catapult":
                        nouvelle_tour = Catapult(id=tour_id, position=pos_tour)
                    elif self.type_selectionne == "mage":
                        nouvelle_tour = TourMage(id=tour_id, position=pos_tour)
                    elif self.type_selectionne == "Feu de camp":
                        nouvelle_tour = FeuDeCamps(id=tour_id, position=pos_tour)
                    else:
                        # Types non encore implémentés
                        nouvelle_tour = None
                    if nouvelle_tour is not None:

                        self.tours.append(nouvelle_tour)
                        self.positions_occupees[case]["instance"] = nouvelle_tour

                        # Joue le son du feu de camp si c'est un feu de camp
                        if self.type_selectionne == "Feu de camp":
                            try:
                                campfire_sound = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "audio", "bruitage", "camp-fire.mp3"))
                                campfire_sound.play().set_volume(0.15)
                            except Exception:
                                pass

                        # Mémorise le prix d'achat pour revente éventuelle
                        self.positions_occupees[case]["prix"] = getattr(
                            nouvelle_tour,
                            "prix",
                            self.prix_par_type.get(self.type_selectionne, 0),
                        )

                    # Débiter le prix correspondant
                    self.joueur.argent -= self.prix_par_type.get(self.type_selectionne, 0)
                    self.type_selectionne = None
                    self.tour_selectionnee = None  # désélectionne la range

        # Clic droit: vendre une tour posée (si on clique sur une case occupée)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            pos = event.pos
            # On ignore si on clique dans la zone boutique
            if self.rect_boutique.collidepoint(pos):
                self.tour_selectionnee = None  # désélectionne la range
                return None
            if self._position_dans_grille(pos):
                case = self._case_depuis_pos(pos)
                if case and case in self.positions_occupees:
                    # Prix payé mémorisé au placement; remboursement = moitié (arrondi bas)
                    prix_achat = int(self.positions_occupees[case].get("prix", 0))
                    remboursement = prix_achat // 2
                    self.joueur.argent += remboursement
                    # Retire l'instance de tour à cet emplacement (centre de case)
                    cx = case[0] * self.taille_case + self.taille_case // 2
                    cy = case[1] * self.taille_case + self.taille_case // 2
                    self.tours = [t for t in self.tours if not (int(t.position.x) == cx and int(t.position.y) == cy)]
                    # Libère la case pour placement futur
                    del self.positions_occupees[case]
                    self.tour_selectionnee = None  # désélectionne la range

        return None

    # ---------- Vagues ----------
    def lancerVague(self):
        """Démarre une nouvelle vague d'ennemis, chargée depuis un CSV."""
        self.numVague += 1
        self.debutVague = pygame.time.get_ticks()
        print("Vague n°", self.numVague, "lancée")

        # Génère la liste d'ennemis depuis le CSV (la fabrique gère leurs types)
        self.ennemis = creer_liste_ennemis_depuis_csv(self.numVague)
        # Désactive le callback d'arrivée au château (les dégâts sont gérés sur les cases (3,0) et (4,0))
        for e in self.ennemis:
            try:
                setattr(e, "_on_reach_castle", None)
            except Exception:
                pass

        # Si aucune donnée CSV, on peut au moins spawner un gobelin de base
        if not self.ennemis:
            gob = Gobelin(id=1, tmj_path=self.tmj_path)
            if hasattr(gob, "apparaitre"):
                gob.apparaitre()
            # Désactive le callback d'arrivée pour le fallback
            try:
                setattr(gob, "_on_reach_castle", None)
            except Exception:
                pass
            self.ennemis = [gob]

    def majvague(self):
        """Fait apparaître les ennemis au moment de leur temps d'apparition."""
        if not self.ennemis:
            return
        now = pygame.time.get_ticks()
        elapsed_s = round((now - self.debutVague) / 1000, 1)
        for e in self.ennemis:
            try:
                if getattr(e, "tempsApparition", None) is not None and elapsed_s == e.tempsApparition:
                    if hasattr(e, "apparaitre"):
                        e.apparaitre()
            except Exception:
                # Si l'ennemi ne supporte pas l'apparition temporisée, on ignore
                pass

    # ---------- Chemin / placement ----------
    def _cases_depuis_chemin(self, chemin_positions: list[Position]) -> set[tuple[int, int]]:
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
        if not self.ennemis:
            return True
        for e in self.ennemis:
            est_mort = getattr(e, "estMort", lambda: False)()
            au_bout = getattr(e, "a_atteint_le_bout", lambda: False)()
            if not (est_mort or au_bout):
                return False
        return True

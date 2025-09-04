from __future__ import annotations

import os
import pygame

from classes.pointeur import Pointeur
from classes.ennemi import Gobelin, Ennemi  # Gobelin + type de base
from classes.joueur import Joueur
from classes.position import Position
from classes.tour import Archer, Catapult, Tour
from classes.projectile import ProjectileFleche, ProjectilePierre
from classes.utils import charger_chemin_tiled
from classes.csv import creer_liste_ennemis_depuis_csv

base_dir = os.path.dirname(os.path.dirname(__file__))


class Game:
    def __init__(self, police: pygame.font.Font):
        self.joueur = Joueur(argent=100, point_de_vie=100, sort="feu", etat="normal")
        self.police = police

        # Grille / carte
        self.taille_case = 64
        self.colonnes = 12
        self.lignes = 12
        self.largeur_ecran = 768
        self.hauteur_ecran = 768
        self.case_survolee: tuple[int, int] | None = None

        # Boutique (à droite de la carte)
        self.largeur_boutique = 400
        self.rect_boutique = pygame.Rect(self.largeur_ecran, 0, self.largeur_boutique, self.hauteur_ecran)
        self.prix_tour = 10

        # Animation monnaie
        self.coin_frames = self._charger_piece()
        self.coin_frame_idx = 0
        self.COIN_ANIM_INTERVAL = 120
        self.last_coin_ticks = pygame.time.get_ticks()

        # Animation coeurs (PV)
        self.heart_frames = self._charger_coeurs()
        self.heart_frame_idx = 0
        self.HEART_ANIM_INTERVAL = 120
        self.last_heart_ticks = pygame.time.get_ticks()

        # Types de tours
        self.tower_types = ["archer", "catapult", "mage"]
        self.tower_assets = self._charger_tours()
        self.shop_items = self._creer_boutons_boutique()
        self.type_selectionne: str | None = None

        # Occupation des cases (affichage)
        self.positions_occupees: dict[tuple[int, int], dict] = {}

        # Tours / projectiles (logique)
        self.tours: list[Tour] = []
        self.projectiles: list[ProjectileFleche | ProjectilePierre] = []

        # Images projectiles
        self.image_fleche = self._charger_image_projectile(getattr(ProjectileFleche, "CHEMIN_IMAGE", ""))
        self.image_pierre = self._charger_image_projectile(getattr(ProjectilePierre, "CHEMIN_IMAGE", ""))

        # Couleurs UI
        # Projectiles actifs (flèches, etc.)
        # Peut contenir ProjectileFleche et ProjectilePierre
        self.projectiles: list = []
        # Images de base des projectiles (chargées via une fonction générique)
        self.image_fleche = self._charger_image_projectile(ProjectileFleche.CHEMIN_IMAGE)
        self.image_pierre = self._charger_image_projectile(ProjectilePierre.CHEMIN_IMAGE)
        self.couleur_quadrillage = (100, 100, 100)
        self.couleur_surbrillance = (255, 255, 0)
        self.couleur_surbrillance_interdite = (255, 80, 80)
        self.couleur_boutique_bg = (30, 30, 30)
        self.couleur_boutique_border = (80, 80, 80)
        self.couleur_bouton_bg = (60, 60, 60)
        self.couleur_bouton_hover = (90, 90, 90)
        self.couleur_texte = (240, 240, 240)

        # Carte / chemin
        self.clock = pygame.time.Clock()
        self.carte = self._charger_carte()
        self.tmj_path = os.path.join(base_dir, "assets", "tilesets", "carte.tmj")
        chemin_positions = charger_chemin_tiled(self.tmj_path, layer_name="path")
        self.cases_bannies = self._cases_depuis_chemin(chemin_positions)
        # Bannir aussi les 6 cases des deux premières lignes (x=0..5, y=0..1)
        for y in (0, 1):
            for x in range(0, 6):
                if 0 <= x < self.colonnes and 0 <= y < self.lignes:
                    self.cases_bannies.add((x, y))

        # Pointeur
        self.pointeur = Pointeur()

        # Gestion des vagues
        self.numVague = 0
        self.debutVague = 0
        self.ennemis: list[Ennemi] = []  # Rempli lors du lancement de vague

    # ---------- Chargements ----------
    def _charger_carte(self):
        chemin_carte = os.path.join(base_dir, "assets", "tilesets", "carte.png")
        if not os.path.exists(chemin_carte):
            raise FileNotFoundError(f"Carte non trouvée: {chemin_carte}")
        img = pygame.image.load(chemin_carte).convert_alpha()
        return img

    def _charger_piece(self):
        coinImg = os.path.join(base_dir, "assets", "money", "MonedaD.png")
        if os.path.exists(coinImg):
            img = pygame.image.load(coinImg).convert_alpha()
            w, h = img.get_width(), img.get_height()
            col_w = max(1, w // 5)
            frames = [img.subsurface(pygame.Rect(col_w * i, 0, col_w, h)).copy() for i in range(5)]
            frames = [pygame.transform.smoothscale(f, (24, 24)) for f in frames]
            return frames
        return []

    def _charger_coeurs(self):
        """Charge toutes les images de coeur dans assets/heart et retourne une liste de surfaces."""
        frames = []
        dossier = os.path.join(base_dir, "assets", "heart")
        if not os.path.isdir(dossier):
            return frames
        fichiers = [f for f in os.listdir(dossier) if f.lower().endswith(".png")]
        if not fichiers:
            return frames
        fichiers.sort()
        for fn in fichiers:
            p = os.path.join(dossier, fn)
            try:
                img = pygame.image.load(p).convert_alpha()
                frames.append(img)
            except Exception:
                continue
        return frames

    def _charger_tours(self):
        assets = {}
        for tower_type in self.tower_types:
            dossier = os.path.join("assets", "tower", tower_type)
            dossier_absolu = os.path.join(base_dir, dossier)
            if not os.path.isdir(dossier_absolu):
                continue
            chemins = [f for f in os.listdir(dossier_absolu) if f.endswith(".png")]
            if not chemins:
                continue
            chemins.sort()
            dernier_chemin = os.path.join(dossier_absolu, chemins[-1])
            image = pygame.image.load(dernier_chemin).convert_alpha()
            w, h = image.get_width(), image.get_height()
            col_w = w // 4
            slices = [image.subsurface(pygame.Rect(col_w * i, 0, col_w, h)) for i in range(4)]
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

        p = os.path.join(base_dir, chemin_relatif)
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
        ecran.blit(txt_solde, (self.rect_boutique.x + 50, 56))

        # Points de vie
        coeur_pos = (self.rect_boutique.x + 120, 60)
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
            hover = rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(
                ecran,
                self.couleur_bouton_hover if hover else self.couleur_bouton_bg,
                rect,
                border_radius=6,
            )
            pygame.draw.rect(ecran, self.couleur_boutique_border, rect, 2, border_radius=6)
            t = item["type"]

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
            prix_val = self.prix_tour
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

        if self.type_selectionne:
            info = self.police.render(f"Place: {self.type_selectionne}", True, (200, 220, 255))
            ecran.blit(info, (self.rect_boutique.x + 20, self.hauteur_ecran - 40))

    def _dessiner_surbrillance(self, ecran):
        if not self.case_survolee:
            return
        x_case, y_case = self.case_survolee
        rect = pygame.Rect(x_case * self.taille_case, y_case * self.taille_case, self.taille_case, self.taille_case)
        overlay = pygame.Surface((self.taille_case, self.taille_case), pygame.SRCALPHA)
        interdit = (
            (x_case, y_case) in getattr(self, "cases_bannies", set())
            or (x_case, y_case) in self.positions_occupees
        )
        couleur = self.couleur_surbrillance_interdite if interdit else self.couleur_surbrillance
        overlay.fill((*couleur, 80))
        if rect.right <= self.largeur_ecran:
            ecran.blit(overlay, rect)

    def _dessiner_tours_placees(self, ecran):
        """Dessine l'apparence des tours sur la grille (assets ou fallback)."""
        for (x_case, y_case), data in self.positions_occupees.items():
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
                    e.majVisible()
                if hasattr(e, "draw"):
                    e.draw(ecran)

    # ---------- Update / boucle ----------
    def maj(self, dt: float):
        # Apparition des ennemis selon la vague
        self.majvague()

        # Déplacement des ennemis actifs
        for e in self.ennemis:
            try:
                if not hasattr(e, "estApparu") or e.estApparu(self.debutVague):
                    e.seDeplacer(dt)
            except Exception:
                # Si l'ennemi ne supporte pas le timing des vagues, on le met à jour quand même
                if hasattr(e, "seDeplacer"):
                    e.seDeplacer(dt)

        # Mise à jour des tours (acquisitions + tirs)
        for t in self.tours:
            def au_tir(tour: Tour, cible: Gobelin):
                if isinstance(tour, Archer) and self.image_fleche is not None:
                    p = ProjectileFleche(origine=tour.position, cible_pos=cible.position.copy())
                    p.cible = cible  # head-seeking
                    p.image_base = self.image_fleche
                    self.projectiles.append(p)
                elif isinstance(tour, Catapult) and self.image_pierre is not None:
                    p = ProjectilePierre(origine=tour.position, cible_pos=cible.position.copy())
                    p.cible = cible
                    p.image_base = self.image_pierre
                    self.projectiles.append(p)

            if hasattr(t, "maj"):
                t.maj(dt, self.ennemis, au_tir=au_tir)

        # Mise à jour projectiles + collisions
        for pr in self.projectiles:
            if hasattr(pr, "mettreAJour"):
                pr.mettreAJour(dt)
            if getattr(pr, "detruit", False):
                continue
            for e in self.ennemis:
                if hasattr(e, "estMort") and e.estMort():
                    continue
                if hasattr(pr, "aTouche") and pr.aTouche(e):
                    if hasattr(pr, "appliquerDegats"):
                        pr.appliquerDegats(e)
                    break

        # Nettoyage projectiles
        self.projectiles = [p for p in self.projectiles if not getattr(p, "detruit", False)]

    def dessiner(self, ecran: pygame.Surface) -> None:
        dt = self.clock.tick(60) / 1000.0
        ecran.blit(self.carte, (0, 0))
        self._dessiner_tours_placees(ecran)
        self._dessiner_personnages_tours(ecran)
        self._dessiner_surbrillance(ecran)
        self._dessiner_boutique(ecran)
        self.dessiner_ennemis(ecran)

        # Dessine les projectiles au-dessus de la carte (et sous le pointeur)
        for pr in self.projectiles:
            if hasattr(pr, "dessiner"):
                pr.dessiner(ecran)

        self.pointeur.draw(ecran)
        self.maj(dt)

    # ---------- Evénements ----------
    def gerer_evenement(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "PAUSE"

        if event.type == pygame.MOUSEMOTION:
            pos = pygame.mouse.get_pos()
            if self._position_dans_grille(pos):
                self.case_survolee = self._case_depuis_pos(pos)
            else:
                self.case_survolee = None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            # Clic dans la boutique
            if self.rect_boutique.collidepoint(pos):
                for item in self.shop_items:
                    if item["rect"].collidepoint(pos):
                        if self.joueur.argent >= self.prix_tour:
                            self.type_selectionne = item["type"]
                        else:
                            self.type_selectionne = None
                        break
                return None

            # Placement de tour
            if self.type_selectionne and self._position_dans_grille(pos):
                case = self._case_depuis_pos(pos)
                if (
                    case
                    and case not in self.positions_occupees
                    and self.joueur.argent >= self.prix_tour
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
                    if self.type_selectionne == "archer":
                        self.tours.append(Archer(id=tour_id, position=pos_tour))
                    elif self.type_selectionne == "catapult":
                        self.tours.append(Catapult(id=tour_id, position=pos_tour))
                    else:
                        # Types non encore implémentés
                        pass

                    self.joueur.argent -= self.prix_tour
                    self.type_selectionne = None

        return None

    # ---------- Vagues ----------
    def lancerVague(self):
        """Démarre une nouvelle vague d'ennemis, chargée depuis un CSV."""
        self.numVague += 1
        self.debutVague = pygame.time.get_ticks()
        print("Vague n°", self.numVague, "lancée")

        # Génère la liste d'ennemis depuis le CSV (la fabrique gère leurs types)
        self.ennemis = creer_liste_ennemis_depuis_csv(self.numVague)

        # Si aucune donnée CSV, on peut au moins spawner un gobelin de base
        if not self.ennemis:
            gob = Gobelin(id=1, tmj_path=self.tmj_path)
            if hasattr(gob, "apparaitre"):
                gob.apparaitre()
            self.ennemis = [gob]

    def majvague(self):
        """Fait apparaître les ennemis au moment de leur temps d'apparition."""
        if not self.ennemis:
            return
        now = pygame.time.get_ticks()
        elapsed_s = round((now - self.debutVague) / 1000)
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
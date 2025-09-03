import pygame
import os

# ------------------- GAME (SCÈNE DE JEU) -------------------
base_dir = os.path.dirname(os.path.dirname(__file__))

class Game:
    """
    Scène de jeu avec:
    - Carte 12x12 (64px par case) affichée en fond
    - Quadrillage + surbrillance au survol
    - Panneau boutique à droite: achat et placement de tours
    """
    def __init__(self, police: pygame.font.Font):
        self.police = police
        
        # Configuration de la grille (768x768)
        self.taille_case = 64
        self.colonnes = 12
        self.lignes = 12
        
        # Surbrillance
        self.case_survolee = None
        
        # Carte de fond
        self.carte = self._charger_carte()
        
        # Panneau boutique (sur la droite)
        self.largeur_ecran = 768
        self.hauteur_ecran = 768
        self.largeur_boutique = 400
        self.rect_boutique = pygame.Rect(768, 16, 400, 736)
        
        # Argent joueur
        self.solde = 100
        self.prix_tour = 10
        self.coin_image = self._charger_piece()
        
        # Types de tours et assets
        self.tower_types = ["archer", "catapult", "guardian", "mage"]
        # {type: {frames: [[surfaces_decoupees_par_colonne] pour 1..7], icon: surface}}
        self.tower_assets = self._charger_tours()
        
        # Boutons boutique
        self.shop_items = self._creer_boutons_boutique()
        
        # Sélection et placement
        self.type_selectionne = None  # str du type sélectionné pour placement
        self.positions_occupees = {}  # (x_case, y_case) -> {type, frame_idx}
        
        # Couleurs
        self.couleur_quadrillage = (100, 100, 100)
        self.couleur_surbrillance = (255, 255, 0)
        self.couleur_boutique_bg = (30, 30, 30)
        self.couleur_boutique_border = (80, 80, 80)
        self.couleur_bouton_bg = (60, 60, 60)
        self.couleur_bouton_hover = (90, 90, 90)
        self.couleur_texte = (240, 240, 240)

    # ------------------- Chargements -------------------
    def _charger_carte(self):
        chemin_carte = os.path.join(base_dir, "assets", "tilesets", "carte.png")
        if not os.path.exists(chemin_carte):
            raise FileNotFoundError(f"Carte non trouvée: {chemin_carte}")
        img = pygame.image.load(chemin_carte).convert_alpha()
        print(f"Carte chargée: {chemin_carte}")
        return img
    
    def _charger_piece(self):
        # Le nom exact varie; on essaie plusieurs variantes sans planter si introuvable
        candidats = [
            "assets/money/MoneydaD.png",
            "assets/money/MonedaD.png",
        ]
        for p in candidats:
            if os.path.exists(p):
                return pygame.image.load(p).convert_alpha()
        # Fallback visuel simple (cercle) si pas d'asset trouvé
        surf = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 215, 0), (12, 12), 12)
        return surf
    
    def _charger_tours(self):
        assets = {}
        for tower_type in self.tower_types:
            dossier = os.path.join("assets", "tower", tower_type)
            chemins = [f for f in os.listdir(os.path.join(base_dir, dossier)) if f.endswith(".png")]
            if chemins:
                chemins.sort()
                dernier_chemin = os.path.join(base_dir, dossier, chemins[-1])
                image = pygame.image.load(dernier_chemin).convert_alpha()
                w, h = image.get_width(), image.get_height()
                col_w = w // 4
                slices = [image.subsurface(pygame.Rect(col_w * i, 0, col_w, h)) for i in range(4)]
                frames = [slices]
                icon = pygame.transform.smoothscale(slices[2], (48, 48))
                assets[tower_type] = {"frames": frames, "icon": icon}

        return assets

    # ------------------- Boutique -------------------
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

    # ------------------- Utilitaires -------------------
    def _position_dans_grille(self, pos):
        return pos[0] < self.largeur_ecran and 0 <= pos[1] < self.hauteur_ecran
    
    def _case_depuis_pos(self, pos):
        x_case = pos[0] // self.taille_case
        y_case = pos[1] // self.taille_case
        if 0 <= x_case < self.colonnes and 0 <= y_case < self.lignes:
            return (x_case, y_case)
        return None

    # ------------------- Dessins -------------------
    def _dessiner_quadrillage(self, ecran):
        largeur_draw = self.largeur_ecran
        for x in range(0, largeur_draw + 1, self.taille_case):
            pygame.draw.line(ecran, self.couleur_quadrillage, (x, 0), (x, self.hauteur_ecran))
        for y in range(0, self.hauteur_ecran + 1, self.taille_case):
            pygame.draw.line(ecran, self.couleur_quadrillage, (0, y), (largeur_draw, y))

    def _dessiner_boutique(self, ecran):
        # Fond et bordure
        pygame.draw.rect(ecran, self.couleur_boutique_bg, self.rect_boutique)
        pygame.draw.rect(ecran, self.couleur_boutique_border, self.rect_boutique, 2)
        
        # Titre
        titre = self.police.render("Boutique", True, self.couleur_texte)
        ecran.blit(titre, (self.rect_boutique.x + (self.largeur_boutique - titre.get_width()) // 2, 20))
        
        # Solde
        coin = pygame.transform.smoothscale(self.coin_image, (24, 24))
        ecran.blit(coin, (self.rect_boutique.x + 20, 60))
        txt_solde = self.police.render(f"{self.solde}", True, self.couleur_texte)
        ecran.blit(txt_solde, (self.rect_boutique.x + 50, 56))
        
        # Boutons tours
        for item in self.shop_items:
            rect = item["rect"]
            hover = rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(ecran, self.couleur_bouton_hover if hover else self.couleur_bouton_bg, rect, border_radius=6)
            pygame.draw.rect(ecran, self.couleur_boutique_border, rect, 2, border_radius=6)
            t = item["type"]
            label = self.police.render(t.capitalize(), True, self.couleur_texte)
            ecran.blit(label, (rect.x + 70, rect.y + 10))
            prix = self.police.render(f"{self.prix_tour}", True, self.couleur_texte)
            ecran.blit(prix, (rect.right - 30, rect.y + 10))
            if t in self.tower_assets:
                ecran.blit(self.tower_assets[t]["icon"], (rect.x + 10, rect.y + 10))

        # Indication de sélection
        if self.type_selectionne:
            info = self.police.render(f"Place: {self.type_selectionne}", True, (200, 220, 255))
            ecran.blit(info, (self.rect_boutique.x + 20, self.hauteur_ecran - 40))

    def _dessiner_surbrillance(self, ecran):
        if not self.case_survolee:
            return
        x_case, y_case = self.case_survolee
        rect = pygame.Rect(x_case * self.taille_case, y_case * self.taille_case, self.taille_case, self.taille_case)
        overlay = pygame.Surface((self.taille_case, self.taille_case), pygame.SRCALPHA)
        overlay.fill((*self.couleur_surbrillance, 80))
        # Ne pas dessiner sur la boutique
        if rect.right <= self.largeur_ecran:
            ecran.blit(overlay, rect)

    def _dessiner_tours_placees(self, ecran):
        for (x_case, y_case), data in self.positions_occupees.items():
            ttype = data["type"]
            surf = None
            if ttype in self.tower_assets and self.tower_assets[ttype]["frames"]:
                # Toujours prendre la 3ème tranche (index 2)
                slices = self.tower_assets[ttype]["frames"][0]
                surf = slices[2]
                surf = pygame.transform.smoothscale(surf, (self.taille_case, self.taille_case))
            if surf is None:
                surf = pygame.Surface((self.taille_case, self.taille_case))
                surf.fill((150, 150, 180))
            ecran.blit(surf, (x_case * self.taille_case, y_case * self.taille_case))

    # ------------------- API scène -------------------
    def dessiner(self, ecran: pygame.Surface) -> None:
        # Carte
        ecran.blit(self.carte, (0, 0))
        # Quadrillage limité à la zone de jeu (hors boutique)
        # Tours placées
        self._dessiner_tours_placees(ecran)
        # Surbrillance
        self._dessiner_surbrillance(ecran)
        # Boutique
        self._dessiner_boutique(ecran)

    def gerer_evenement(self, event: pygame.event.Event) -> str | None:
        # Pause
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "PAUSE"
        
        # Mise à jour survol case
        if event.type == pygame.MOUSEMOTION:
            pos = pygame.mouse.get_pos()
            if self._position_dans_grille(pos):
                self.case_survolee = self._case_depuis_pos(pos)
            else:
                self.case_survolee = None
        
        # Clics
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            # Clic dans boutique -> sélection
            if self.rect_boutique.collidepoint(pos):
                for item in self.shop_items:
                    if item["rect"].collidepoint(pos):
                        if self.solde >= self.prix_tour:
                            self.type_selectionne = item["type"]
                        else:
                            self.type_selectionne = None
                        break
                return None
            # Clic placement dans la grille
            if self.type_selectionne and self._position_dans_grille(pos):
                case = self._case_depuis_pos(pos)
                if case and case not in self.positions_occupees and self.solde >= self.prix_tour:
                    # Place la tour et débite
                    self.positions_occupees[case] = {"type": self.type_selectionne, "frame": 0}
                    self.solde -= self.prix_tour
                    # Fin sélection après placement
                    self.type_selectionne = None
        return None

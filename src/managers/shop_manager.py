import os
from typing import TYPE_CHECKING, Tuple

import pygame

from classes.constants import (
    COIN_ANIM_INTERVAL_MS,
    HEART_ANIM_INTERVAL_MS,
    MONEY_DIR,
    SHOP_WIDTH,
    SPELLS_HEIGHT,
)
from classes.sprites import charger_animation_ui, charger_spritesheet_ui

if TYPE_CHECKING:
    from game import Game


class ShopManager:
    """Manager pour gérer toutes les boutiques (tours et sorts)."""

    def __init__(self, game: "Game"):
        self.game = game

        # Boutique des tours (à droite de la carte)
        self.largeur_boutique = SHOP_WIDTH
        self.rect_boutique = pygame.Rect(
            game.largeur_ecran, 0, self.largeur_boutique, game.hauteur_ecran
        )

        # Boutique de sorts (en bas de l'écran)
        self.hauteur_boutique_sorts = SPELLS_HEIGHT
        self.rect_boutique_sorts = pygame.Rect(
            0,
            game.hauteur_ecran,
            game.largeur_ecran + self.largeur_boutique,
            self.hauteur_boutique_sorts,
        )

        # Items de la boutique des tours
        self.shop_items = self._creer_boutons_boutique()

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

        # Couleurs UI
        self.couleur_boutique_bg = (30, 30, 30)
        self.couleur_boutique_border = (80, 80, 80)
        self.couleur_bouton_bg = (60, 60, 60)
        self.couleur_bouton_hover = (90, 90, 90)
        self.couleur_texte = (240, 240, 240)
        self.couleur_boutique_sorts_bg = self.couleur_boutique_bg
        self.couleur_boutique_sorts_border = self.couleur_boutique_border

    def _charger_piece(self):
        """Charge l'animation des pièces depuis MonedaD.png (spritesheet)."""
        coinImg = os.path.join(MONEY_DIR, "MonedaD.png")
        frames = charger_spritesheet_ui(coinImg, 5, scale=1.0)
        # Redimensionner à 24x24
        if frames:
            frames = [pygame.transform.smoothscale(f, (24, 24)) for f in frames]
        return frames

    def _charger_coeurs(self):
        """Charge toutes les images de coeur en utilisant la fonction utilitaire."""
        return charger_animation_ui("heart", scale=1.0)

    def _creer_boutons_boutique(self):
        """Crée les boutons de la boutique des tours."""
        boutons = []
        x = self.rect_boutique.x + 20
        y = 100
        espace_y = 90
        for t in self.game.tower_types:
            rect = pygame.Rect(x, y, self.largeur_boutique - 40, 70)
            boutons.append({"type": t, "rect": rect})
            y += espace_y
        return boutons

    def dessiner_boutique_tours(self, ecran: pygame.Surface) -> None:
        """Dessine la boutique des tours."""
        pygame.draw.rect(ecran, self.couleur_boutique_bg, self.rect_boutique)
        pygame.draw.rect(ecran, self.couleur_boutique_border, self.rect_boutique, 2)
        titre = self.game.police.render("Boutique", True, self.couleur_texte)
        ecran.blit(
            titre,
            (
                self.rect_boutique.x + (self.largeur_boutique - titre.get_width()) // 2,
                20,
            ),
        )

        # Monnaie - chiffre puis icône (icône à droite)
        txt_solde = self.game.police.render(
            f"{self.game.joueur.argent}", True, self.couleur_texte
        )
        ecran.blit(txt_solde, (self.rect_boutique.x + 20, 56))

        if self.coin_frames:
            coin = self.coin_frames[self.coin_frame_idx % len(self.coin_frames)]
            # Positionner l'icône à droite du texte
            coin_x = self.rect_boutique.x + 20 + txt_solde.get_width() + 5
            ecran.blit(coin, (coin_x, 60))
            now = pygame.time.get_ticks()
            if now - self.last_coin_ticks >= self.COIN_ANIM_INTERVAL:
                self.coin_frame_idx = (self.coin_frame_idx + 1) % len(self.coin_frames)
                self.last_coin_ticks = now

        # Points de vie - chiffre puis icône (icône à droite)
        txt_pv = self.game.police.render(
            f"{self.game.joueur.point_de_vie}", True, self.couleur_texte
        )
        # Positionner le texte des PV à droite de la monnaie
        pv_x = self.rect_boutique.x + 140
        ecran.blit(txt_pv, (pv_x, 56))

        if self.heart_frames:
            coeur = self.heart_frames[self.heart_frame_idx % len(self.heart_frames)]
            coeur_s = pygame.transform.smoothscale(coeur, (24, 24))
            # Positionner l'icône à droite du texte
            coeur_x = pv_x + txt_pv.get_width() + 5
            ecran.blit(coeur_s, (coeur_x, 60))
            now = pygame.time.get_ticks()
            if now - self.last_heart_ticks >= self.HEART_ANIM_INTERVAL:
                self.heart_frame_idx = (self.heart_frame_idx + 1) % len(
                    self.heart_frames
                )
                self.last_heart_ticks = now
        else:
            # Petit fallback visuel si aucun asset
            coeur_x = pv_x + txt_pv.get_width() + 5
            pygame.draw.circle(ecran, (220, 50, 50), (coeur_x + 12, 72), 12)

        # Boutons tours
        for item in self.shop_items:
            rect = item["rect"]
            t = item["type"]
            hover = rect.collidepoint(pygame.mouse.get_pos())
            # Fond hover si sélectionné
            if self.game.type_selectionne == t or hover:
                couleur_fond_boutton = self.couleur_bouton_hover
            else:
                couleur_fond_boutton = self.couleur_bouton_bg
            pygame.draw.rect(
                ecran,
                couleur_fond_boutton,
                rect,
                border_radius=6,
            )
            pygame.draw.rect(
                ecran, self.couleur_boutique_border, rect, 2, border_radius=6
            )

            # label centré verticalement
            label = self.game.police_tour.render(
                t.capitalize(), True, self.couleur_texte
            )
            label_y = rect.y + (rect.h - label.get_height()) // 2

            # icône (si disponible) centrée verticalement
            icon = None
            if t in self.game.tower_assets:
                icon = self.game.tower_assets[t].get("icon")
            if icon:
                icon_y = rect.y + (rect.h - icon.get_height()) // 2
                ecran.blit(icon, (rect.x + 10, icon_y))

            # position du label (après icône)
            label_x = rect.x + 70
            ecran.blit(label, (label_x, label_y))

            # prix : aligné à droite et centré verticalement, couleur selon solvabilité
            prix_val = self.game.tour_manager.prix_par_type.get(t, 0)
            can_buy = self.game.joueur.argent >= prix_val
            prix_color = (240, 240, 240) if can_buy else (220, 80, 80)
            prix = self.game.police.render(f"{prix_val}", True, prix_color)

            # icône de pièce
            coin_w, coin_h = 20, 20
            if self.coin_frames:
                coin_frame = self.coin_frames[
                    self.coin_frame_idx % len(self.coin_frames)
                ]
                try:
                    coin_surf = pygame.transform.smoothscale(
                        coin_frame, (coin_w, coin_h)
                    )
                except Exception:
                    coin_surf = coin_frame
            else:
                coin_surf = pygame.Surface((coin_w, coin_h), pygame.SRCALPHA)
                pygame.draw.circle(
                    coin_surf, (220, 200, 40), (coin_w // 2, coin_h // 2), coin_w // 2
                )

            # aligne prix au bord droit du bouton, coin à sa gauche
            gap = 6
            prix_x = rect.right - 10 - prix.get_width()
            coin_x = prix_x - gap - coin_surf.get_width()

            # centrage vertical
            prix_y = rect.y + (rect.h - prix.get_height()) // 2
            coin_y = rect.y + (rect.h - coin_surf.get_height()) // 2

            # dessin: icône puis prix (prix à droite)
            if coin_surf:
                ecran.blit(coin_surf, (coin_x, coin_y))
            ecran.blit(prix, (prix_x, prix_y))

        # Bouton de vague
        bouton_actif = self.game.ennemi_manager.vague_terminee()
        if bouton_actif:
            self.game.bouton_vague.dessiner(ecran)
        else:
            # Dessin grisé
            old_couleurs = self.game.bouton_vague.couleurs.copy()
            self.game.bouton_vague.couleurs["fond_normal"] = (120, 120, 120)
            self.game.bouton_vague.couleurs["fond_survol"] = (160, 160, 160)
            self.game.bouton_vague.couleurs["texte"] = (180, 180, 180)
            self.game.bouton_vague.dessiner(ecran)
            self.game.bouton_vague.couleurs = old_couleurs

        # Affiche le numéro de vague au-dessus du bouton
        try:
            label_vague = self.game.police.render(
                f"Vague n° {self.game.ennemi_manager.num_vague}",
                True,
                self.couleur_texte,
            )
            label_x = (
                self.game.bouton_vague.rect.x
                + (self.game.bouton_vague.rect.w - label_vague.get_width()) // 2
            )
            label_y = self.game.bouton_vague.rect.y - 36
            ecran.blit(label_vague, (label_x, label_y))
        except Exception:
            pass

    def dessiner_boutique_sorts(self, ecran: pygame.Surface) -> None:
        """Dessine la boutique de sorts en bas de l'écran."""
        pygame.draw.rect(
            ecran, self.couleur_boutique_sorts_bg, self.rect_boutique_sorts
        )
        pygame.draw.rect(
            ecran, self.couleur_boutique_sorts_border, self.rect_boutique_sorts, 2
        )

        # Titre de la boutique de sorts
        titre = self.game.police.render("Boutique de sorts", True, self.couleur_texte)
        ecran.blit(
            titre,
            (
                self.rect_boutique_sorts.x
                + (self.rect_boutique_sorts.width - titre.get_width()) // 2,
                self.rect_boutique_sorts.y + 20,
            ),
        )

        # Affichage des sorts disponibles
        y_offset = 60
        x_offset = 20

        for sort_key, sort in self.game.sorts.items():
            # Rectangle pour le sort (même style que la boutique)
            sort_rect = pygame.Rect(
                self.rect_boutique_sorts.x + x_offset,
                self.rect_boutique_sorts.y + y_offset,
                300,
                80,
            )

            # Vérifier si le sort est au niveau maximum
            is_max_level = (
                hasattr(sort, "est_au_niveau_maximum") and sort.est_au_niveau_maximum()
            )

            # Pour le sort de la fée, vérifier s'il est déjà actif
            is_fee_active = (
                sort_key == "fee" and hasattr(sort, "est_actif") and sort.est_actif()
            )

            # Pour l'éclair, vérifier s'il est sélectionné
            is_eclair_selected = (
                sort_key == "eclair"
                and hasattr(self.game, "eclair_selectionne")
                and self.game.eclair_selectionne
            )

            # Effet de survol (comme dans la boutique)
            hover = sort_rect.collidepoint(pygame.mouse.get_pos())
            can_buy = (
                sort.peut_etre_achete(self.game.joueur.argent)
                and not is_max_level
                and not is_fee_active
                and not is_eclair_selected
            )

            if hover and can_buy:
                couleur_fond = self.couleur_bouton_hover
            else:
                couleur_fond = self.couleur_bouton_bg

            # Dessin avec bordures arrondies (comme la boutique)
            pygame.draw.rect(ecran, couleur_fond, sort_rect, border_radius=6)
            pygame.draw.rect(
                ecran, self.couleur_boutique_sorts_border, sort_rect, 2, border_radius=6
            )

            # Nom du sort avec niveau (style boutique)
            if is_max_level or is_fee_active or is_eclair_selected:
                # Grisé quand au niveau maximum, quand la fée est active, ou quand l'éclair est sélectionné
                nom_sort = self.game.police.render(
                    sort.nom_complet, True, (120, 120, 120)
                )
            else:
                nom_sort = self.game.police.render(
                    sort.nom_complet, True, self.couleur_texte
                )
            ecran.blit(nom_sort, (sort_rect.x + 10, sort_rect.y + 10))

            # Prix et icône seulement si pas au niveau maximum, pas actif, et pas sélectionné
            if not is_max_level and not is_fee_active and not is_eclair_selected:
                # Prix avec couleur selon solvabilité (comme la boutique)
                prix_color = self.couleur_texte if can_buy else (220, 80, 80)
                prix_text = self.game.police.render(f"{sort.prix}", True, prix_color)

                # Icône de pièce (comme la boutique)
                coin_w, coin_h = 20, 20
                if self.coin_frames:
                    coin_frame = self.coin_frames[
                        self.coin_frame_idx % len(self.coin_frames)
                    ]
                    try:
                        coin_surf = pygame.transform.smoothscale(
                            coin_frame, (coin_w, coin_h)
                        )
                    except Exception:
                        coin_surf = coin_frame
                else:
                    coin_surf = pygame.Surface((coin_w, coin_h), pygame.SRCALPHA)
                    pygame.draw.circle(
                        coin_surf,
                        (220, 200, 40),
                        (coin_w // 2, coin_h // 2),
                        coin_w // 2,
                    )

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
                max_text = self.game.police.render("MAX", True, (100, 200, 100))
                max_x = sort_rect.right - 10 - max_text.get_width()
                max_y = sort_rect.y + 40
                ecran.blit(max_text, (max_x, max_y))
            elif is_fee_active:
                # Afficher "ACTIF" pour la fée
                actif_text = self.game.police.render("ACTIF", True, (100, 200, 100))
                actif_x = sort_rect.right - 10 - actif_text.get_width()
                actif_y = sort_rect.y + 40
                ecran.blit(actif_text, (actif_x, actif_y))
            elif is_eclair_selected:
                # Afficher "SÉLECTIONNÉ" pour l'éclair
                selected_text = self.game.police.render(
                    "SÉLECTIONNÉ", True, (255, 200, 0)
                )
                selected_x = sort_rect.right - 10 - selected_text.get_width()
                selected_y = sort_rect.y + 40
                ecran.blit(selected_text, (selected_x, selected_y))

            x_offset += 320  # Espacement entre les sorts

    def gerer_clic_boutique_tours(self, pos: Tuple[int, int]) -> bool:
        """Gère les clics dans la boutique des tours. Retourne True si un clic a été traité."""
        if not self.rect_boutique.collidepoint(pos):
            return False

        for item in self.shop_items:
            if item["rect"].collidepoint(pos):
                # Sélectionne le type uniquement si le joueur a assez d'argent
                t = item["type"]
                prix_t = self.game.tour_manager.prix_par_type.get(t, 0)

                # Si déjà sélectionné, on désélectionne
                if self.game.type_selectionne == t:
                    self.game.type_selectionne = None
                elif self.game.joueur.argent >= prix_t:
                    self.game.type_selectionne = t
                    self.game.eclair_selectionne = False  # Désélectionner l'éclair
                else:
                    self.game.type_selectionne = None
                return True
        return False

    def gerer_clic_boutique_sorts(self, pos: Tuple[int, int]) -> bool:
        """Gère les clics dans la boutique des sorts. Retourne True si un clic a été traité."""
        if not self.rect_boutique_sorts.collidepoint(pos):
            return False

        x_offset = 20
        for sort_key, sort in self.game.sorts.items():
            sort_rect = pygame.Rect(
                self.rect_boutique_sorts.x + x_offset,
                self.rect_boutique_sorts.y + 60,
                300,
                80,
            )
            if sort_rect.collidepoint(pos):
                # Vérifier si le sort n'est pas au niveau maximum
                is_max_level = (
                    hasattr(sort, "est_au_niveau_maximum")
                    and sort.est_au_niveau_maximum()
                )
                # Vérifier si la fée n'est pas déjà active
                is_fee_active = (
                    sort_key == "fee"
                    and hasattr(sort, "est_actif")
                    and sort.est_actif()
                )

                if sort_key == "eclair":
                    # Pour l'éclair, sélectionner/désélectionner le sort
                    if self.game.eclair_selectionne:
                        # Si déjà sélectionné, le désélectionner
                        self.game.eclair_selectionne = False
                    elif not is_max_level and sort.peut_etre_achete(
                        self.game.joueur.argent
                    ):
                        # Sinon, le sélectionner si on peut l'acheter
                        self.game.eclair_selectionne = True
                        self.game.type_selectionne = None  # Désélectionner les tours
                elif not is_max_level and not is_fee_active:
                    achat_ok = sort.acheter(self.game.joueur)
                    if achat_ok and sort_key == "fee":
                        # Son d'activation de la fée
                        self.game.jouer_sfx("magic-spell.mp3")
                return True
            x_offset += 320
        return False

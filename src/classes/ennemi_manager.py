import os
from typing import TYPE_CHECKING

import pygame

from classes.csv import creer_liste_ennemis_depuis_csv
from classes.ennemi import Ennemi
from classes.constants import PROJECT_ROOT, RECOMPENSES_PAR_VAGUE

if TYPE_CHECKING:
    from game import Game


class EnnemiManager:
    """Manager pour gérer tous les aspects liés aux ennemis."""
    
    def __init__(self, game: "Game"):
        self.game = game
        self.ennemis: list[Ennemi] = []
        self.num_vague = 0
        self.debut_vague = 0
        
        # Gestion de l'état jour/nuit
        self.est_nuit = False
    
    def lancer_vague(self) -> None:
        """Démarre une nouvelle vague d'ennemis, chargée depuis un CSV."""
        self.num_vague += 1
        self.debut_vague = pygame.time.get_ticks()
        
        # Active l'effet de nuit pendant la vague
        self.est_nuit = True
        
        print("Vague n°", self.num_vague, "lancée")
        
        # Génère la liste d'ennemis depuis le CSV
        self.ennemis = creer_liste_ennemis_depuis_csv(self.num_vague)
        
        for e in self.ennemis:
            try:
                setattr(e, "_on_reach_castle", None)
            except Exception:
                pass
    
    def mettre_a_jour_vague(self) -> None:
        """Fait apparaître les ennemis au moment de leur temps d'apparition."""
        if not self.ennemis:
            return
        now = pygame.time.get_ticks()
        elapsed_s = round((now - self.debut_vague) / 1000, 1)
        for e in self.ennemis:
            try:
                if (
                    hasattr(e, "tempsApparition")
                    and elapsed_s >= e.tempsApparition
                    and not getattr(e, "estApparu", lambda x: False)(self.debut_vague)
                ):
                    e.estApparu = lambda x: True
            except Exception:
                pass
    
    def mettre_a_jour_ennemis(self, dt: float) -> None:
        """Met à jour tous les ennemis actifs."""
        # Déplacement des ennemis actifs
        for e in self.ennemis:
            try:
                if not hasattr(e, "estApparu") or e.estApparu(self.debut_vague):
                    e.seDeplacer(dt)
                    e.update_animation(dt)
            except Exception:
                if hasattr(e, "seDeplacer"):
                    e.seDeplacer(dt)
        
        # Perte de PV si un ennemi touche certaines cases "château"
        for e in self.ennemis:
            try:
                pos_px = (int(e.position.x), int(e.position.y))
                case = self._case_depuis_pos(pos_px)
                if case in {(2, 0), (3, 0)}:
                    deg = getattr(e, "degats", 1)
                    self.game.joueur.point_de_vie = max(
                        0, int(self.game.joueur.point_de_vie) - int(deg)
                    )
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
    
    def _ennemi_atteint_chateau(self, ennemi: Ennemi, pos_px: tuple = None) -> bool:
        """Vérifie si un ennemi a atteint le château."""
        if pos_px is None:
            pos_px = (int(ennemi.position.x), int(ennemi.position.y))
        
        # Vérifier si l'ennemi est arrivé au bout du chemin
        if hasattr(ennemi, "a_atteint_le_bout") and ennemi.a_atteint_le_bout():
            return True
        
        # Vérifier les cases spéciales du château
        case_x = pos_px[0] // 64
        case_y = pos_px[1] // 64
        
        # Cases spéciales qui causent des dégâts au joueur
        cases_chateau = [(20, 8), (21, 8), (22, 8), (23, 8), (24, 8)]
        
        return (case_x, case_y) in cases_chateau
    
    def _ennemi_atteint_chateau(self, ennemi: Ennemi) -> None:
        """Gère les dégâts quand un ennemi atteint le château."""
        # Inflige les dégâts de l'ennemi au joueur lorsque l'ennemi atteint la fin
        try:
            deg = getattr(ennemi, "degats", 1)
        except Exception:
            deg = 1
        
        self.game.joueur.pointsDeVie -= deg
        
        # Le marquer comme "mort" pour que les tours cessent de le cibler
        try:
            ennemi.pointsDeVie = 0
        except Exception:
            pass
    
    def dessiner_ennemis(self, ecran: pygame.Surface) -> None:
        """Dessine tous les ennemis actifs."""
        for e in self.ennemis:
            # Compat : certains ennemis peuvent avoir des états (apparu/mort/arrivé)
            try:
                doit_dessiner = (
                    (not hasattr(e, "estApparu") or e.estApparu(self.debut_vague))
                    and not getattr(e, "estMort", lambda: False)()
                    and not getattr(e, "a_atteint_le_bout", lambda: False)()
                )
                
                if doit_dessiner:
                    e.draw(ecran)
                    
                    # Dessiner la barre de vie si l'ennemi a perdu des PV
                    if (
                        hasattr(e, "pointsDeVie")
                        and hasattr(e, "pointsDeVieMax")
                        and e.pointsDeVie < e.pointsDeVieMax
                    ):
                        # Position de la barre : juste au-dessus de l'ennemi
                        px = int(e.position.x)
                        py = int(e.position.y)
                        
                        # Dimensions de la barre
                        largeur_max = 40
                        hauteur = 6
                        
                        # Calculer le pourcentage de vie
                        pourcentage_vie = e.pointsDeVie / e.pointsDeVieMax
                        largeur_actuelle = int(largeur_max * pourcentage_vie)
                        
                        x_barre = px - largeur_max // 2
                        y_barre = py - 40  # Espace entre le haut du sprite et l'ennemi
                        
                        # Fond gris
                        pygame.draw.rect(
                            ecran, (60, 60, 60), (x_barre, y_barre, largeur_max, hauteur)
                        )
                        
                        # Barre de vie verte
                        couleur_vie = (0, 255, 0) if pourcentage_vie > 0.5 else (255, 255, 0) if pourcentage_vie > 0.25 else (255, 0, 0)
                        pygame.draw.rect(
                            ecran, couleur_vie, (x_barre, y_barre, largeur_actuelle, hauteur)
                        )
                        
            except Exception:
                pass
    
    def gerer_collisions_projectiles(self, projectiles: list) -> None:
        """Gère les collisions entre projectiles et ennemis."""
        for pr in projectiles:
            if not isinstance(pr, type(None)) and hasattr(pr, "detruit") and not pr.detruit:
                # Collision projectiles tours -> ennemis
                for e in self.ennemis:
                    if hasattr(e, "estMort") and e.estMort():
                        continue
                    
                    if hasattr(pr, "aTouche") and pr.aTouche(e):
                        # Gestion spéciale pour les projectiles de mage avec dégâts de zone
                        if hasattr(pr, "__class__") and "ProjectileTourMage" in str(pr.__class__):
                            # Appliquer les dégâts de zone à tous les ennemis dans la zone
                            pr.appliquerDegatsZone(self.ennemis)
                            # Marquer le projectile comme détruit
                            pr.detruit = True
                        else:
                            # Dégâts normaux
                            e.perdreVie(pr.degats)
                            pr.detruit = True
                            
                            # Son d'impact
                            if hasattr(self.game, "jouer_sfx"):
                                self.game.jouer_sfx("arrow-hit-metal.mp3", volume=0.5)
                        
                        # Gestion des récompenses pour tous les ennemis morts
                        for ennemi in self.ennemis:
                            try:
                                if (
                                    ennemi.estMort()
                                    and not getattr(ennemi, "_recompense_donnee", False)
                                    and not getattr(ennemi, "_ne_pas_recompenser", False)
                                ):
                                    self.game.joueur.argent += int(getattr(ennemi, "argent", 0))
                                    setattr(ennemi, "_recompense_donnee", True)
                            except Exception:
                                pass
                        break
    
    def nettoyer_ennemis_morts(self) -> None:
        """Supprime les ennemis morts de la liste."""
        self.ennemis = [
            e
            for e in self.ennemis
            if not (
                getattr(e, "estMort", lambda: False)()
                or getattr(e, "a_atteint_le_bout", lambda: False)()
            )
        ]
    
    def get_ennemis_actifs(self) -> list[Ennemi]:
        """Retourne la liste des ennemis actifs (non morts)."""
        return [e for e in self.ennemis if not getattr(e, "estMort", lambda: False)()]
    
    def get_mages_actifs(self) -> list[Ennemi]:
        """Retourne la liste des mages actifs."""
        from classes.ennemi import Mage
        return [
            e
            for e in self.ennemis
            if isinstance(e, Mage)
            and not e.estMort()
            and (not hasattr(e, "estApparu") or e.estApparu(self.debut_vague))
        ]
    
    def vague_terminee(self) -> bool:
        """Retourne True si tous les ennemis sont morts ou arrivés au bout."""
        if not self.ennemis:
            return True
        for e in self.ennemis:
            est_mort = getattr(e, "estMort", lambda: False)()
            au_bout = getattr(e, "a_atteint_le_bout", lambda: False)()
            if not est_mort and not au_bout:
                return False
        return True
    
    def gerer_fin_vague(self) -> None:
        """Gère la fin de vague : désactive la nuit et donne les récompenses."""
        if self.vague_terminee() and self.est_nuit:
            self.est_nuit = False
            recompense = RECOMPENSES_PAR_VAGUE.get(self.num_vague, 0)
            self.game.joueur.argent += recompense
            print(f"Vague {self.num_vague} terminée ! Récompense : {recompense} pièces")
    
    def est_victoire(self) -> bool:
        """Vérifie si le joueur a gagné (toutes les vagues terminées)."""
        max_vague = self.get_max_vague_csv()
        # Debug
        print(f"Debug victoire: num_vague={self.num_vague}, max_vague={max_vague}, vague_terminee={self.vague_terminee()}")
        # Le joueur a gagné s'il a terminé la dernière vague ET qu'il a au moins lancé une vague
        return self.num_vague > 0 and self.num_vague >= max_vague and self.vague_terminee()
    
    def get_max_vague_csv(self) -> int:
        """Retourne le nombre maximum de vagues disponibles dans le CSV."""
        import csv
        max_vague = 0
        try:
            with open(os.path.join(PROJECT_ROOT, "src", "data", "jeu.csv"), newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    try:
                        num = int(row.get('numVague', 0))
                        if num > max_vague:
                            max_vague = num
                    except Exception:
                        continue
        except Exception:
            pass
        return max_vague
    
    
    def _case_depuis_pos(self, pos):
        """Calcule la case de grille à partir d'une position en pixels."""
        x_case = pos[0] // self.game.taille_case
        y_case = pos[1] // self.game.taille_case
        if 0 <= x_case < self.game.colonnes and 0 <= y_case < self.game.lignes:
            return (x_case, y_case)
        return None
    
    def reset(self) -> None:
        """Remet le manager à zéro."""
        self.ennemis = []
        self.num_vague = 0
        self.debut_vague = 0

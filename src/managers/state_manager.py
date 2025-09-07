from enum import Enum
from typing import Any, Callable, Dict, Optional

import pygame
from classes.menu import afficher_regles
from classes.constants import WINDOW_WIDTH
from classes.menu import (
    creer_boutons_credits,
    creer_boutons_menu,
    dessiner_credits,
    dessiner_menu,
)


class GameState(Enum):
    """États possibles du jeu."""

    MENU = "MENU"
    JEU = "JEU"
    PAUSE = "PAUSE"
    CREDITS = "CREDITS"
    GAMEOVER = "GAMEOVER"
    REGLES = "REGLES"


class StateManager:
    """Manager pour gérer les états du jeu de manière centralisée."""

    def __init__(self, police: pygame.font.Font, game_instance: Any):
        self.police = police
        self.game = game_instance
        self.current_state = GameState.MENU
        self.previous_state: Optional[GameState] = None

        # Configuration des états
        self._state_configs = self._setup_state_configs()

        # Callbacks d'action
        self._callbacks = self._setup_callbacks()

        # Boutons pour chaque état
        self._buttons = self._setup_buttons()

    def _setup_state_configs(self) -> Dict[GameState, Dict[str, Any]]:
        """Configure les paramètres de chaque état."""
        return {
            GameState.MENU: {
                "can_pause": False,
                "can_show_credits": True,
                "can_quit": True,
                "needs_game_update": False,
            },
            GameState.JEU: {
                "can_pause": True,
                "can_show_credits": False,
                "can_quit": False,
                "needs_game_update": True,
            },
            GameState.PAUSE: {
                "can_pause": False,
                "can_show_credits": True,
                "can_quit": True,
                "needs_game_update": True,  # Pour le décompte du temps
            },
            GameState.CREDITS: {
                "can_pause": False,
                "can_show_credits": False,
                "can_quit": False,
                "needs_game_update": False,
            },
            GameState.GAMEOVER: {
                "can_pause": False,
                "can_show_credits": True,
                "can_quit": True,
                "needs_game_update": True,  # Pour figer le temps
            },
        }

    def _setup_callbacks(self) -> Dict[str, Callable]:
        """Configure les callbacks d'action."""
        return {
            "demarrer_jeu": self._demarrer_jeu,
            "reprendre_jeu": self._reprendre_jeu,
            "afficher_credits": self._afficher_credits,
            "afficher_regles": self._afficher_regles,
            "retour_depuis_credits": self._retour_depuis_credits,
            "basculer_muet": self._basculer_muet,
            "redemarrer_partie": self._redemarrer_partie,
            "quitter_jeu": self._quitter_jeu,
        }

    def _setup_buttons(self) -> Dict[GameState, list]:
        """Configure les boutons pour chaque état."""
        # Actions pour chaque menu
        actions_menu_principal = {
            "jouer": self._callbacks["demarrer_jeu"],
            "regles": self._callbacks["afficher_regles"],
            "credits": self._callbacks["afficher_credits"],
            "muet": self._callbacks["basculer_muet"],
            "quitter": self._callbacks["quitter_jeu"],
        }

        actions_menu_pause = {
            "reprendre": self._callbacks["reprendre_jeu"],
            "regles": self._callbacks["afficher_regles"],
            "credits": self._callbacks["afficher_credits"],
            "muet": self._callbacks["basculer_muet"],
            "quitter": self._callbacks["quitter_jeu"],
        }

        actions_gameover = {
            "recommencer": self._callbacks["redemarrer_partie"],
            "credits": self._callbacks["afficher_credits"],
            "quitter": self._callbacks["quitter_jeu"],
        }

        # Création des boutons
        try:
            from classes.menu import creer_boutons_gameover
            from classes.menu import creer_boutons_regles

            buttons_gameover = creer_boutons_gameover(self.police, actions_gameover)
        except ImportError:
            buttons_gameover = []

        return {
            GameState.MENU: creer_boutons_menu(
                self.police, reprendre=False, actions=actions_menu_principal
            ),
            GameState.PAUSE: creer_boutons_menu(
                self.police, reprendre=True, actions=actions_menu_pause
            ),
            GameState.CREDITS: creer_boutons_credits(
                self.police, action_retour=self._callbacks["retour_depuis_credits"]
            ),
            GameState.GAMEOVER: buttons_gameover,
            GameState.JEU: [],  # Pas de boutons pour l'état de jeu
            GameState.REGLES: creer_boutons_regles(self.police, self._retour_depuis_regles),
        }

    def change_state(self, new_state: GameState) -> bool:
        """Change l'état du jeu avec validation."""
        if self._is_valid_transition(self.current_state, new_state):
            self.previous_state = self.current_state
            self.current_state = new_state
            return True
        return False

    def _is_valid_transition(self, from_state: GameState, to_state: GameState) -> bool:
        """Vérifie si une transition d'état est valide."""
        # Règles de transition
        valid_transitions = {
            GameState.MENU: [GameState.JEU, GameState.CREDITS, GameState.REGLES],
            GameState.JEU: [GameState.PAUSE, GameState.GAMEOVER],
            GameState.PAUSE: [GameState.JEU, GameState.CREDITS, GameState.REGLES],
            GameState.CREDITS: [
                GameState.MENU,
                GameState.PAUSE,
                GameState.JEU,
                GameState.GAMEOVER,
                GameState.REGLES,
            ],
            GameState.GAMEOVER: [GameState.JEU, GameState.CREDITS, GameState.REGLES],
            GameState.REGLES: [GameState.MENU, GameState.PAUSE, GameState.JEU, GameState.CREDITS, GameState.GAMEOVER],
        }

        return to_state in valid_transitions.get(from_state, [])

    def get_current_state(self) -> GameState:
        """Retourne l'état actuel."""
        return self.current_state

    def get_previous_state(self) -> Optional[GameState]:
        """Retourne l'état précédent."""
        return self.previous_state

    def get_buttons(self) -> list:
        """Retourne les boutons de l'état actuel."""
        return self._buttons.get(self.current_state, [])

    def needs_game_update(self) -> bool:
        """Vérifie si l'état actuel nécessite une mise à jour du jeu."""
        config = self._state_configs.get(self.current_state, {})
        return config.get("needs_game_update", False)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Gère un événement selon l'état actuel."""
        # Gestion de la musique via l'AudioManager
        try:
            self.game.audio_manager.gerer_evenement_musique(event)
        except Exception:
            pass

        # Gestion des événements selon l'état
        if self.current_state == GameState.JEU:
            changement = self.game.gerer_evenement(event)
            if changement == "PAUSE":
                self.change_state(GameState.PAUSE)
        elif self.current_state == GameState.PAUSE:
            # Gestion de la touche R pour les règles en pause
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self._afficher_regles()
            else:
                # Gestion des boutons pour la pause
                for button in self.get_buttons():
                    button.gerer_evenement(event)
        elif self.current_state == GameState.REGLES:
            for button in self.get_buttons():
                button.gerer_evenement(event)
        else:
            # Gestion des boutons pour les autres états
            for button in self.get_buttons():
                button.gerer_evenement(event)

    def update(self) -> None:
        """Met à jour l'état actuel."""
        if self.current_state == GameState.JEU:
            # Détection Game Over
            try:
                if getattr(self.game.joueur, "point_de_vie", 1) <= 0:
                    self.change_state(GameState.GAMEOVER)
            except Exception:
                pass

    def render(self, screen: pygame.Surface) -> None:
        """Affiche l'état actuel."""
        if self.current_state == GameState.MENU:
            dessiner_menu(screen, self.get_buttons())
        elif self.current_state == GameState.PAUSE:
            self.game.decompte_dt()
            dessiner_menu(screen, self.get_buttons())
        elif self.current_state == GameState.CREDITS:
            dessiner_credits(screen, self.police, WINDOW_WIDTH)
            for button in self.get_buttons():
                button.dessiner(screen)
        elif self.current_state == GameState.JEU:
            self.game.dessiner(screen)
        elif self.current_state == GameState.GAMEOVER:
            self.game.decompte_dt()
            self._render_gameover(screen)
        elif self.current_state == GameState.REGLES:
            afficher_regles(screen, self.police, WINDOW_WIDTH, self.get_buttons())
    def _afficher_regles(self) -> None:
        self.change_state(GameState.REGLES)

    def _render_gameover(self, screen: pygame.Surface) -> None:
        """Affiche l'écran de Game Over."""
        try:
            from classes.menu import dessiner_gameover

            dessiner_gameover(screen, self.get_buttons())
        except ImportError:
            # Fallback si la fonction n'existe pas
            screen.fill((0, 0, 0))
            txt = self.police.render("Game Over", True, (255, 0, 0))
            screen.blit(txt, (screen.get_width() // 2 - txt.get_width() // 2, 200))
            for button in self.get_buttons():
                button.dessiner(screen)

    # Callbacks d'action
    def _demarrer_jeu(self) -> None:
        """Démarre le jeu."""
        self.change_state(GameState.JEU)

    def _reprendre_jeu(self) -> None:
        """Reprend le jeu depuis la pause."""
        self.change_state(GameState.JEU)

    def _afficher_credits(self) -> None:
        """Affiche les crédits."""
        self.change_state(GameState.CREDITS)

    def _retour_depuis_regles(self):
        """Retourne depuis les règles vers l'état précédent."""
        if self.previous_state and self.previous_state != GameState.REGLES:
            self.change_state(self.previous_state)
        else:
            self.change_state(GameState.MENU)    

    def _retour_depuis_credits(self) -> None:
        """Retourne depuis les crédits."""
        if self.previous_state and self.previous_state != GameState.CREDITS:
            self.change_state(self.previous_state)
        else:
            self.change_state(GameState.MENU)

    def _basculer_muet(self) -> None:
        """Bascule l'état muet."""
        try:
            self.game.audio_manager.basculer_muet()
        except Exception:
            pass

    def _redemarrer_partie(self) -> None:
        """Redémarre une nouvelle partie."""
        # Recréer le jeu
        from game import Game

        self.game = Game(self.police, est_muet=self.game.audio_manager.est_muet)
        self.game.audio_manager.demarrer_musique_de_fond()
        self.change_state(GameState.JEU)

    def _quitter_jeu(self) -> None:
        """Quitte le jeu."""
        pygame.quit()
        import sys

        sys.exit()

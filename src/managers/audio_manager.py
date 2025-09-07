import os
import random
from typing import TYPE_CHECKING, Dict

import pygame

from classes.constants import AUDIO_DIR

if TYPE_CHECKING:
    from game import Game


class AudioManager:
    """Manager pour gérer tous les aspects audio du jeu."""
    
    def __init__(self, game: "Game"):
        self.game = game
        self.est_muet = False
        self._sons_cache: Dict[str, pygame.mixer.Sound] = {}
        self.derniere_piste = None  # piste jouée précédemment
        self.volume_musique = 1.0
        
        # Initialisation du mixer pygame
        self._initialiser_mixer()
        
        # Configuration de l'événement pour musique terminée
        self.MUSIQUE_FINIE = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.MUSIQUE_FINIE)
    
    def _initialiser_mixer(self) -> None:
        """Initialise le mixer pygame pour la gestion audio."""
        try:
            pygame.mixer.init()
            self.mixer_disponible = True
        except Exception:
            # Si pas de périphérique audio dispo, on continue sans mixer
            self.mixer_disponible = False
    
    def set_muet(self, muet: bool) -> None:
        """Active ou désactive le mode muet."""
        self.est_muet = muet
        # Met à jour le volume de la musique en cours
        self.set_volume_musique(self.volume_musique)
    
    def jouer_sfx(self, fichier: str, volume: float = 1.0) -> None:
        """Joue un son ponctuel depuis assets/audio/bruitage en respectant l'état muet."""
        try:
            if self.est_muet or not self.mixer_disponible:
                return
            
            chemin = os.path.join(AUDIO_DIR, "bruitage", fichier)
            if not os.path.exists(chemin):
                return
            
            # Utiliser le cache pour éviter de recharger les sons
            if fichier not in self._sons_cache:
                self._sons_cache[fichier] = pygame.mixer.Sound(chemin)
            
            son = self._sons_cache[fichier]
            son.set_volume(volume)
            son.play()
            
        except Exception:
            # On ignore silencieusement les erreurs audio (pas de périphérique, etc.)
            pass
    
    def jouer_musique(self, fichier: str, volume: float = 1.0, loop: int = -1) -> None:
        """Joue une musique de fond."""
        try:
            if self.est_muet or not self.mixer_disponible:
                return
            
            chemin = os.path.join(AUDIO_DIR, fichier)
            if not os.path.exists(chemin):
                return
            
            pygame.mixer.music.load(chemin)
            pygame.mixer.music.set_volume(0.0 if self.est_muet else volume)
            pygame.mixer.music.play(loop)
            
        except Exception:
            pass
    
    def arreter_musique(self) -> None:
        """Arrête la musique de fond."""
        try:
            if self.mixer_disponible:
                pygame.mixer.music.stop()
        except Exception:
            pass
    
    def set_volume_musique(self, volume: float) -> None:
        """Définit le volume de la musique de fond."""
        self.volume_musique = volume
        try:
            if self.mixer_disponible:
                pygame.mixer.music.set_volume(0.0 if self.est_muet else volume)
        except Exception:
            pass
    
    def precharger_son(self, fichier: str) -> None:
        """Précharge un son dans le cache."""
        try:
            if not self.mixer_disponible:
                return
            
            chemin = os.path.join(AUDIO_DIR, "bruitage", fichier)
            if os.path.exists(chemin) and fichier not in self._sons_cache:
                self._sons_cache[fichier] = pygame.mixer.Sound(chemin)
                
        except Exception:
            pass
    
    def precharger_sons_communs(self) -> None:
        """Précharge les sons les plus utilisés pour améliorer les performances."""
        sons_communs = [
            "arrow.mp3",
            "arrow-hit-metal.mp3",
            "catapult.mp3",
            "fire-magic.mp3",
            "explosion-pierre.mp3",
            "loud-thunder.mp3",
            "magic-spell.mp3",
            "wind-magic.mp3",
            "camp-fire.mp3"
        ]
        
        for son in sons_communs:
            self.precharger_son(son)
    
    def vider_cache(self) -> None:
        """Vide le cache des sons pour libérer la mémoire."""
        self._sons_cache.clear()
    
    def get_statistiques(self) -> Dict[str, int]:
        """Retourne des statistiques sur l'utilisation audio."""
        return {
            "sons_en_cache": len(self._sons_cache),
            "mixer_disponible": self.mixer_disponible,
            "mode_muet": self.est_muet
        }
    
    def demarrer_musique_de_fond(self) -> None:
        """Choisit une musique aléatoirement et la joue."""
        if not self.mixer_disponible:
            return
            
        pistes_candidates = [
            "Aqua-Barbie-Girl.mp3",
            "Camila-Cabello-Havana.mp3",
            "Crab-Rave-medieval-style.mp3",
            "Nirvana-Smells-Like-Teen-Spirit.mp3",
            "Shakira-Hips-Don-t-Lie.mp3",
            "We-Found-Love-Bardcore.mp3",
        ]

        # Filtrer celles qui existent vraiment
        pistes_existantes = []
        for piste in pistes_candidates:
            chemin = os.path.join(AUDIO_DIR, piste)
            if os.path.exists(chemin):
                pistes_existantes.append(piste)
                
        if not pistes_existantes:
            return

        # Choisir une piste différente de la précédente
        choix = random.choice(pistes_existantes)
        while len(pistes_existantes) > 1 and choix == self.derniere_piste:
            choix = random.choice(pistes_existantes)

        self.derniere_piste = choix
        self.jouer_musique(choix, self.volume_musique)
    
    def gerer_evenement_musique(self, event: pygame.event.Event) -> None:
        """Gère l'événement de fin de musique pour relancer automatiquement."""
        if event.type == self.MUSIQUE_FINIE:
            self.demarrer_musique_de_fond()
    
    def basculer_muet(self) -> None:
        """Bascule l'état muet."""
        self.set_muet(not self.est_muet)
    
    def nettoyer(self) -> None:
        """Nettoie les ressources audio."""
        try:
            if self.mixer_disponible:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
        except Exception:
            pass
        self.vider_cache()

"""
Constantes partagées pour le projet Protect The Castle.
Ce module centralise chemins, tailles et couleurs utilisées par plusieurs modules.
"""

import os
from typing import Dict, Tuple

# Racine du projet (dossier contenant `src`)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
TILESETS_DIR = os.path.join(ASSETS_DIR, "tilesets")
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")
MONEY_DIR = os.path.join(ASSETS_DIR, "money")
HEART_DIR = os.path.join(ASSETS_DIR, "heart")
TOWER_DIR = os.path.join(ASSETS_DIR, "tower")

# Ecran / grille
TILE_SIZE: int = 64
GRID_COLS: int = 12
GRID_ROWS: int = 12
GAME_WIDTH: int = TILE_SIZE * GRID_COLS  # 768
GAME_HEIGHT: int = TILE_SIZE * GRID_ROWS  # 768
SHOP_WIDTH: int = 400
SPELLS_HEIGHT: int = 200
WINDOW_WIDTH: int = GAME_WIDTH + SHOP_WIDTH  # 1168
WINDOW_HEIGHT: int = GAME_HEIGHT + SPELLS_HEIGHT
FPS: int = 60
GAME_NAME: str = "Protect The Castle"

# Couleurs UI (R, G, B)
COLORS: Dict[str, Tuple[int, int, int]] = {
    "background": (0, 6, 25),
    "border": (40, 40, 60),
    "text": (200, 220, 255),
    "grid": (40, 60, 100),
    "highlight": (80, 180, 255),
    "highlight_forbidden": (255, 80, 80),
    "shop_bg": (30, 30, 30),
    "shop_border": (80, 80, 80),
    "button_bg": (60, 60, 60),
    "button_hover": (90, 90, 90),
    "ui_text": (240, 240, 240),
}

# Timings (millisecondes)
COIN_ANIM_INTERVAL_MS: int = 120
HEART_ANIM_INTERVAL_MS: int = 120

# Chemins de fichiers fréquemment utilisés
MAP_TILESET_TMJ: str = os.path.join(TILESETS_DIR, "carte.tmj")
MAP_PNG: str = os.path.join(TILESETS_DIR, "carte.png")

# Valeurs par défaut / listes partagées
DEFAULT_TOWER_TYPES = ["archer", "catapulte", "mage", "campement"]

# Valeurs de récompense par vague
RECOMPENSES_PAR_VAGUE: dict[int, int] = {
    1: 35,
    2: 35,
    3: 30,
    4: 20,
    5: 20,
    6: 15,
    7: 15,
    8: 10,
    9: 30,
    10: 20,
}

# Export
__all__ = [
    "PROJECT_ROOT",
    "ASSETS_DIR",
    "TILESETS_DIR",
    "AUDIO_DIR",
    "MONEY_DIR",
    "HEART_DIR",
    "TOWER_DIR",
    "TILE_SIZE",
    "GRID_COLS",
    "GRID_ROWS",
    "GAME_WIDTH",
    "GAME_HEIGHT",
    "SHOP_WIDTH",
    "WINDOW_WIDTH",
    "WINDOW_HEIGHT",
    "FPS",
    "COLORS",
    "COIN_ANIM_INTERVAL_MS",
    "HEART_ANIM_INTERVAL_MS",
    "MAP_TILESET_TMJ",
    "MAP_PNG",
    "DEFAULT_TOWER_TYPES",
    "GAME_NAME",
    "RECOMPENSES_PAR_VAGUE",
]

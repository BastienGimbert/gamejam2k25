import json
import os
from math import hypot
from typing import List

import pygame

from classes.constants import ASSETS_DIR, PROJECT_ROOT
from classes.position import Position


def distance_positions(a: Position, b: Position) -> float:
    return hypot(a.x - b.x, a.y - b.y)


def charger_chemin_tiled(tmj_path: str, layer_name: str = "path") -> List[Position]:
    """
    Charge les points d'un polygon depuis un calque d'objets dans un fichier .tmj.
    """
    if not os.path.isabs(tmj_path):
        tmj_path = os.path.join(PROJECT_ROOT, tmj_path)
    with open(tmj_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    layer = next(
        (
            l
            for l in data["layers"]
            if l["type"] == "objectgroup" and l["name"] == layer_name
        ),
        None,
    )  # Trouve le calque d'objets correspondant au nom donné
    if not layer:
        raise ValueError(f"Calque '{layer_name}' introuvable dans {tmj_path}")
    obj = next(
        (o for o in layer["objects"] if "polygon" in o), None
    )  # Trouve le premier objet contenant un polygon
    if not obj:
        raise ValueError(f"Aucun polygon trouvé dans le calque '{layer_name}'.")

    ox, oy = obj["x"], obj["y"]
    return [Position(ox + p["x"], oy + p["y"]) for p in obj["polygon"]]


def cases_depuis_chemin(chemin_positions: list[Position], taille_case: int) -> set[tuple[int, int]]:
    """Approxime les cases de grille traversées par le polygone du chemin."""
    bannies: set[tuple[int, int]] = set()
    if not chemin_positions:
        return bannies

    for i in range(len(chemin_positions)):
        p1 = chemin_positions[i]
        p2 = chemin_positions[(i + 1) % len(chemin_positions)]

        # Calculer les cases traversées par le segment
        x1, y1 = int(p1.x), int(p1.y)
        x2, y2 = int(p2.x), int(p2.y)

        # Algorithme de ligne de Bresenham simplifié
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x_step = 1 if x1 < x2 else -1
        y_step = 1 if y1 < y2 else -1

        x, y = x1, y1
        bannies.add((x // taille_case, y // taille_case))

        if dx > dy:
            error = dx / 2
            while x != x2:
                error -= dy
                if error < 0:
                    y += y_step
                    error += dx
                x += x_step
                bannies.add((x // taille_case, y // taille_case))
        else:
            error = dy / 2
            while y != y2:
                error -= dx
                if error < 0:
                    x += x_step
                    error += dy
                y += y_step
                bannies.add((x // taille_case, y // taille_case))

    return bannies


def position_dans_grille(pos: tuple[int, int], largeur_ecran: int, hauteur_ecran: int) -> bool:
    """Vérifie si une position est dans la grille de jeu."""
    return pos[0] < largeur_ecran and 0 <= pos[1] < hauteur_ecran


def case_depuis_pos(pos: tuple[int, int], taille_case: int, colonnes: int, lignes: int) -> tuple[int, int] | None:
    """Convertit une position en coordonnées de case de grille."""
    x_case = pos[0] // taille_case
    y_case = pos[1] // taille_case
    if 0 <= x_case < colonnes and 0 <= y_case < lignes:
        return (x_case, y_case)
    return None



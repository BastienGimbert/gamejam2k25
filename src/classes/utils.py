import json
import os
from math import hypot
from typing import List


from classes.constants import PROJECT_ROOT
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


def cases_depuis_chemin(
    chemin_positions: list[Position], taille_case: int
) -> set[tuple[int, int]]:
    """
    Calcule les cases de grille traversées par un chemin polygonal.
    
    Cette fonction utilise l'algorithme de ligne de Bresenham pour déterminer
    toutes les cases de grille qui sont traversées par un chemin défini par
    une série de points. C'est utilisé pour marquer les cases "interdites"
    où on ne peut pas placer de tours.
    
    Args:
        chemin_positions: Liste des points du chemin (Position)
        taille_case: Taille d'une case en pixels (ex: 64)
        
    Returns:
        Set des coordonnées (x, y) des cases traversées
        
    Exemple:
        chemin = [Position(0, 0), Position(128, 64)]
        cases = cases_depuis_chemin(chemin, 64)
        # Retourne {(0, 0), (1, 0), (2, 1)} pour un chemin diagonal
    """
    cases_traversees: set[tuple[int, int]] = set()
    
    # Vérification des paramètres
    if not chemin_positions or taille_case <= 0:
        return cases_traversees

    # Traiter chaque segment du chemin
    for i in range(len(chemin_positions)):
        p1 = chemin_positions[i]
        p2 = chemin_positions[(i + 1) % len(chemin_positions)]  # Boucle sur le dernier point

        # Convertir les positions en coordonnées entières
        x1, y1 = int(p1.x), int(p1.y)
        x2, y2 = int(p2.x), int(p2.y)

        # ALGORITHME DE LIGNE DE BRESENHAM
        # Cet algorithme trace une ligne pixel par pixel entre deux points
        # et détermine quelles cases de grille sont traversées
        
        # Calculer les différences et directions
        dx = abs(x2 - x1)  # Distance horizontale absolue
        dy = abs(y2 - y1)  # Distance verticale absolue
        x_step = 1 if x1 < x2 else -1  # Direction horizontale (+1 ou -1)
        y_step = 1 if y1 < y2 else -1  # Direction verticale (+1 ou -1)

        # Point de départ
        x, y = x1, y1
        cases_traversees.add((x // taille_case, y // taille_case))

        # Tracer la ligne selon l'orientation dominante
        if dx > dy:
            # Ligne principalement horizontale
            error = dx / 2  # Erreur accumulée pour décider du déplacement vertical
            while x != x2:
                error -= dy
                if error < 0:
                    y += y_step  # Déplacement vertical
                    error += dx  # Réinitialiser l'erreur
                x += x_step  # Déplacement horizontal
                cases_traversees.add((x // taille_case, y // taille_case))
        else:
            # Ligne principalement verticale
            error = dy / 2  # Erreur accumulée pour décider du déplacement horizontal
            while y != y2:
                error -= dx
                if error < 0:
                    x += x_step  # Déplacement horizontal
                    error += dy  # Réinitialiser l'erreur
                y += y_step  # Déplacement vertical
                cases_traversees.add((x // taille_case, y // taille_case))

    return cases_traversees


def position_dans_grille(
    pos: tuple[int, int], largeur_ecran: int, hauteur_ecran: int
) -> bool:
    """Vérifie si une position est dans la grille de jeu."""
    return pos[0] < largeur_ecran and 0 <= pos[1] < hauteur_ecran


def case_depuis_pos(
    pos: tuple[int, int], taille_case: int, colonnes: int, lignes: int
) -> tuple[int, int] | None:
    """Convertit une position en coordonnées de case de grille."""
    x_case = pos[0] // taille_case
    y_case = pos[1] // taille_case
    if 0 <= x_case < colonnes and 0 <= y_case < lignes:
        return (x_case, y_case)
    return None

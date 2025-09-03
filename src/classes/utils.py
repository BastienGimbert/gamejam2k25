

import json
from math import hypot
from git import List
from classes.position import Position

def distance_positions(a: Position, b: Position) -> float:
    return hypot(a.x - b.x, a.y - b.y)

def charger_chemin_tiled(tmj_path: str, layer_name: str = "path") -> List[Position]:
    """
    Charge les points d'un polygon depuis un calque d'objets dans un fichier .tmj.
    """
    with open(tmj_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    layer = next((l for l in data["layers"] if l["type"] == "objectgroup" and l["name"] == layer_name), None)  # Trouve le calque d'objets correspondant au nom donné
    if not layer:  
        raise ValueError(f"Calque '{layer_name}' introuvable dans {tmj_path}")  
    obj = next((o for o in layer["objects"] if "polygon" in o), None)  # Trouve le premier objet contenant un polygon
    if not obj: 
        raise ValueError(f"Aucun polygon trouvé dans le calque '{layer_name}'.") 

    ox, oy = obj["x"], obj["y"]
    return [Position(ox + p["x"], oy + p["y"]) for p in obj["polygon"]] 
import json
from math import hypot
from typing import List
from classes.position import Position
import os
import pygame

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def distance_positions(a: Position, b: Position) -> float:
    return hypot(a.x - b.x, a.y - b.y)

def charger_chemin_tiled(tmj_path: str, layer_name: str = "path") -> List[Position]:
    """
    Charge les points d'un polygon depuis un calque d'objets dans un fichier .tmj.
    """
    if not os.path.isabs(tmj_path):
        tmj_path = os.path.join(base_dir, tmj_path)
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


def decouper_sprite(image: pygame.Surface, nb_images: int, horizontal: bool = True, copy: bool = True) -> list[pygame.Surface]:
    """
    Découpe une spritesheet simple en 'nb_images' parties égales.
    - image: Surface source.
    - nb_images: nombre de frames.
    - horizontal: True si les frames sont alignées horizontalement.
    - copy: si True retourne des copies (indépendantes), sinon des subsurfaces.
    """
    if nb_images <= 0:
        raise ValueError("nb_images doit être > 0")

    w, h = image.get_width(), image.get_height()
    slices: list[pygame.Surface] = []

    if horizontal:
        frame_w = w // nb_images
        if frame_w * nb_images != w:
            raise ValueError("Largeur non divisible par nb_images")
        for i in range(nb_images):
            rect = pygame.Rect(i * frame_w, 0, frame_w, h)
            part = image.subsurface(rect)
            slices.append(part.copy() if copy else part)
    else:
        frame_h = h // nb_images
        if frame_h * nb_images != h:
            raise ValueError("Hauteur non divisible par nb_images")
        for i in range(nb_images):
            rect = pygame.Rect(0, i * frame_h, w, frame_h)
            part = image.subsurface(rect)
            slices.append(part.copy() if copy else part)

    return slices

def charger_et_scaler(sous_dossier: str, nom_fichier: str, nb_frames: int, scale: float = 1.0) -> list[pygame.Surface]:
    """
    Charge une spritesheet, découpe en nb_frames et applique un facteur d'échelle.
    sous_dossier: sous-dossier dans assets/enemy (ex: 'goblin')
    nom_fichier: nom du fichier image (ex: 'D_Walk.png')
    nb_frames: nombre de frames à découper
    scale: facteur d'échelle (1.0 = taille originale)
    """
    chemin = os.path.join(base_dir, "assets", "enemy", sous_dossier, nom_fichier)
    image = pygame.image.load(chemin).convert_alpha()
    frames = decouper_sprite(image, nb_frames)
    if scale != 1.0:
        frames = [pygame.transform.scale(f, (int(f.get_width()*scale), int(f.get_height()*scale))) for f in frames]
    return frames

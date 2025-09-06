import json
import os
from math import hypot
from typing import List, Dict, Optional

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


def decouper_sprite(
    image: pygame.Surface, nb_images: int, horizontal: bool = True, copy: bool = True
) -> list[pygame.Surface]:
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




# Cache global pour les sprites
_sprite_cache: Dict[str, List[pygame.Surface]] = {}


def charger_sprites_directionnels(
    sous_dossier: str, 
    directions: List[str], 
    nom_fichier_pattern: str, 
    nb_frames: int, 
    scale: float = 1.0
) -> Dict[str, List[pygame.Surface]]:
    """
    Charge les sprites pour plusieurs directions en une fois.
    
    Args:
        sous_dossier: Sous-dossier dans assets/enemy (ex: 'goblin')
        directions: Liste des directions (ex: ['D', 'S', 'U'])
        nom_fichier_pattern: Pattern du nom de fichier (ex: '{direction}_Walk.png')
        nb_frames: Nombre de frames à découper
        scale: Facteur d'échelle
    
    Returns:
        Dictionnaire {direction: [frames]}
    """
    result = {}
    
    for direction in directions:
        nom_fichier = nom_fichier_pattern.format(direction=direction)
        cache_key = f"{sous_dossier}_{nom_fichier}_{nb_frames}_{scale}"
        
        # Vérifier le cache
        if cache_key in _sprite_cache:
            result[direction] = _sprite_cache[cache_key]
        else:
            try:
                # Charger l'image et la découper
                chemin = os.path.join(ASSETS_DIR, "enemy", sous_dossier, nom_fichier)
                if os.path.exists(chemin):
                    image = pygame.image.load(chemin).convert_alpha()
                    frames = decouper_sprite(image, nb_frames, horizontal=True, copy=True)
                    
                    # Appliquer le scale si nécessaire
                    if scale != 1.0:
                        frames = [
                            pygame.transform.scale(
                                f, (int(f.get_width() * scale), int(f.get_height() * scale))
                            )
                            for f in frames
                        ]
                    
                    _sprite_cache[cache_key] = frames
                    result[direction] = frames
                else:
                    print(f"Fichier manquant: {chemin}")
                    result[direction] = []
            except Exception as e:
                print(f"Erreur chargement {sous_dossier}/{nom_fichier}: {e}")
                result[direction] = []
    
    return result


def charger_sprites_ui(category: str, scale: float = 1.0) -> List[pygame.Surface]:
    """
    Charge les sprites d'interface utilisateur (pièces, cœurs, etc.).
    
    Args:
        category: Catégorie ('money', 'heart', etc.)
        scale: Facteur d'échelle
    
    Returns:
        Liste des frames
    """
    cache_key = f"ui_{category}_{scale}"
    
    if cache_key in _sprite_cache:
        return _sprite_cache[cache_key]
    
    frames = []
    
    if category == "money":
        # Charger les pièces
        try:
            coin_path = os.path.join(ASSETS_DIR, "money", "MonedaD.png")
            if os.path.exists(coin_path):
                image = pygame.image.load(coin_path).convert_alpha()
                frames = decouper_sprite(image, 5, horizontal=True, copy=True)
                if scale != 1.0:
                    frames = [
                        pygame.transform.scale(
                            f, (int(f.get_width() * scale), int(f.get_height() * scale))
                        )
                        for f in frames
                    ]
        except Exception as e:
            print(f"Erreur chargement pièces: {e}")
    
    elif category == "heart":
        # Charger les cœurs
        try:
            heart_dir = os.path.join(ASSETS_DIR, "heart")
            if os.path.isdir(heart_dir):
                heart_files = [f for f in os.listdir(heart_dir) if f.lower().endswith(".png")]
                heart_files.sort()
                for filename in heart_files:
                    file_path = os.path.join(heart_dir, filename)
                    try:
                        img = pygame.image.load(file_path).convert_alpha()
                        if scale != 1.0:
                            new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                            img = pygame.transform.scale(img, new_size)
                        frames.append(img)
                    except Exception:
                        continue
        except Exception as e:
            print(f"Erreur chargement cœurs: {e}")
    
    _sprite_cache[cache_key] = frames
    return frames


def vider_cache_sprites():
    """Vide le cache des sprites."""
    global _sprite_cache
    _sprite_cache.clear()


def charger_sprite_tour(tour_type: str, scale: float = 1.0) -> pygame.Surface:
    """
    Charge le sprite principal d'une tour (frame 3 de l'image la plus haute).
    
    Args:
        tour_type: Type de tour ('archer', 'catapulte', 'mage')
        scale: Facteur d'échelle
    
    Returns:
        Surface du sprite de la tour
    """
    cache_key = f"tower_{tour_type}_{scale}"
    
    if cache_key in _sprite_cache:
        return _sprite_cache[cache_key]
    
    # Déterminer le fichier le plus haut pour chaque type de tour
    tour_files = {
        "archer": "6.png",  # Le plus grand nombre
        "catapulte": "7.png",  # Le plus grand nombre
        "mage": "5.png",  # Le plus grand nombre
        "campement": "1.png"  # Le campement utilise 1.png
    }
    
    if tour_type not in tour_files:
        return None
    
    try:
        file_path = os.path.join(ASSETS_DIR, "tower", tour_type, tour_files[tour_type])
        if os.path.exists(file_path):
            image = pygame.image.load(file_path).convert_alpha()
            
            if tour_type == "campement":
                # Pour le campement, découper en 6 frames et prendre la dernière (frame 6, index 5)
                frames = decouper_sprite(image, 6, horizontal=True, copy=True)
                if len(frames) >= 6:
                    sprite = frames[5]  # Dernière frame (index 5)
                else:
                    # Fallback si pas assez de frames
                    sprite = frames[-1] if frames else image
            else:
                # Pour les autres tours, découper en 4 frames et prendre la frame 3 (index 2)
                frames = decouper_sprite(image, 4, horizontal=True, copy=True)
                if len(frames) >= 3:
                    sprite = frames[2]  # Frame 3 (index 2)
                else:
                    # Fallback si pas assez de frames
                    sprite = frames[-1] if frames else image
            
            if scale != 1.0:
                new_size = (int(sprite.get_width() * scale), int(sprite.get_height() * scale))
                sprite = pygame.transform.scale(sprite, new_size)
            
            _sprite_cache[cache_key] = sprite
            return sprite
        else:
            print(f"Fichier tour manquant: {file_path}")
            return None
    except Exception as e:
        print(f"Erreur chargement tour {tour_type}: {e}")
        return None


def charger_animation(chemin_relatif: str, nb_frames: int, scale: float = 1.0, horizontal: bool = True) -> List[pygame.Surface]:
    """
    Charge une animation à partir d'un fichier sprite sheet.
    
    Args:
        chemin_relatif: Chemin relatif vers le fichier (ex: "tower/campement/1.png")
        nb_frames: Nombre de frames dans l'animation
        scale: Facteur d'échelle
        horizontal: True si les frames sont disposées horizontalement
    
    Returns:
        Liste des frames d'animation
    """
    cache_key = f"animation_{chemin_relatif}_{nb_frames}_{scale}_{horizontal}"
    
    if cache_key in _sprite_cache:
        return _sprite_cache[cache_key]
    
    try:
        file_path = os.path.join(ASSETS_DIR, chemin_relatif)
        if os.path.exists(file_path):
            image = pygame.image.load(file_path).convert_alpha()
            frames = decouper_sprite(image, nb_frames, horizontal=horizontal, copy=True)
            
            if scale != 1.0:
                frames = [
                    pygame.transform.scale(
                        f, (int(f.get_width() * scale), int(f.get_height() * scale))
                    )
                    for f in frames
                ]
            
            _sprite_cache[cache_key] = frames
            return frames
        else:
            print(f"Fichier animation manquant: {file_path}")
            return []
    except Exception as e:
        print(f"Erreur chargement animation {chemin_relatif}: {e}")
        return []


def charger_animation_campement(scale: float = 1.0) -> List[pygame.Surface]:
    """
    Charge l'animation du campement (6 frames).
    
    Args:
        scale: Facteur d'échelle
    
    Returns:
        Liste des frames d'animation
    """
    return charger_animation("tower/campement/1.png", 6, scale, horizontal=True)


def charger_image_simple(chemin_relatif: str) -> Optional[pygame.Surface]:
    """
    Charge une image simple sans découpage.
    
    Args:
        chemin_relatif: Chemin relatif vers l'image (ex: "fond.png")
    
    Returns:
        Surface de l'image ou None si erreur
    """
    cache_key = f"image_{chemin_relatif}"
    
    if cache_key in _sprite_cache:
        return _sprite_cache[cache_key]
    
    try:
        file_path = os.path.join(ASSETS_DIR, chemin_relatif)
        if os.path.exists(file_path):
            image = pygame.image.load(file_path).convert_alpha()
            _sprite_cache[cache_key] = image
            return image
        else:
            print(f"Image manquante: {file_path}")
            return None
    except Exception as e:
        print(f"Erreur chargement image {chemin_relatif}: {e}")
        return None


def charger_image_projectile(chemin_relatif: str) -> Optional[pygame.Surface]:
    """
    Charge une image de projectile.
    
    Args:
        chemin_relatif: Chemin relatif vers l'image du projectile
    
    Returns:
        Surface de l'image ou None si erreur
    """
    if not chemin_relatif:
        return None
    
    cache_key = f"projectile_{chemin_relatif}"
    
    if cache_key in _sprite_cache:
        return _sprite_cache[cache_key]
    
    try:
        file_path = os.path.join(ASSETS_DIR, chemin_relatif)
        if os.path.exists(file_path):
            image = pygame.image.load(file_path).convert_alpha()
            _sprite_cache[cache_key] = image
            return image
        else:
            print(f"Projectile manquant: {file_path}")
            return None
    except Exception as e:
        print(f"Erreur chargement projectile {chemin_relatif}: {e}")
        return None

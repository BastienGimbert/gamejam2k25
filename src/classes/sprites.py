import os
from typing import List

import pygame

from classes.constants import ASSETS_DIR, PROJECT_ROOT


def decouper_sprite(
    image: pygame.Surface, nb_images: int, horizontal: bool = True, copy: bool = True
) -> list[pygame.Surface]:
    """
    Découpe une spritesheet simple en 'nb_images' parties égales.
    
    Args:
        image: Surface source
        nb_images: Nombre de frames
        horizontal: True si les frames sont alignées horizontalement
        copy: Si True retourne des copies (indépendantes), sinon des subsurfaces
    
    Returns:
        Liste des surfaces découpées
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


def charger_sprites_ennemi(type_ennemi: str, nom_fichier: str, nb_frames: int, scale: float = 1.0) -> list[pygame.Surface]:
    """
    Charge les sprites d'un ennemi de manière uniforme.
    
    Args:
        type_ennemi: Type d'ennemi (ex: 'goblin', 'rat', 'wolf', etc.)
        nom_fichier: Nom du fichier image (ex: 'D_Walk.png')
        nb_frames: Nombre de frames à découper
        scale: Facteur d'échelle (1.0 = taille originale)
    
    Returns:
        Liste des surfaces pygame découpées et redimensionnées
    """
    chemin = os.path.join(ASSETS_DIR, "enemy", type_ennemi, nom_fichier)
    image = pygame.image.load(chemin).convert_alpha()
    frames = decouper_sprite(image, nb_frames)
    if scale != 1.0:
        frames = [
            pygame.transform.scale(
                f, (int(f.get_width() * scale), int(f.get_height() * scale))
            )
            for f in frames
        ]
    return frames


def charger_sprites_tour(type_tour: str, nom_fichier: str, nb_frames: int, scale: float = 1.0) -> list[pygame.Surface]:
    """
    Charge les sprites d'une tour de manière uniforme.
    
    Args:
        type_tour: Type de tour (ex: 'archer', 'catapulte', 'mage', 'campement')
        nom_fichier: Nom du fichier image (ex: '1.png')
        nb_frames: Nombre de frames à découper
        scale: Facteur d'échelle (1.0 = taille originale)
    
    Returns:
        Liste des surfaces pygame découpées et redimensionnées
    """
    chemin = os.path.join(ASSETS_DIR, "tower", type_tour, nom_fichier)
    image = pygame.image.load(chemin).convert_alpha()
    frames = decouper_sprite(image, nb_frames)
    if scale != 1.0:
        frames = [
            pygame.transform.scale(
                f, (int(f.get_width() * scale), int(f.get_height() * scale))
            )
            for f in frames
        ]
    return frames


def charger_image_projectile(chemin_relatif: str) -> pygame.Surface:
    """
    Charge une image de projectile avec fallback en cas d'erreur.
    
    Args:
        chemin_relatif: Chemin relatif vers l'image du projectile
    
    Returns:
        Surface pygame de l'image ou une surface de fallback
    """
    if not chemin_relatif:
        # Fallback simple
        surf = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(surf, (120, 120, 120), (11, 11), 10)
        return surf

    p = os.path.join(PROJECT_ROOT, chemin_relatif)
    if os.path.exists(p):
        try:
            return pygame.image.load(p).convert_alpha()
        except Exception:
            pass
    
    # Fallbacks selon le type de projectile
    if "archer" in chemin_relatif or "arrow" in chemin_relatif:
        surf = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.line(surf, (220, 220, 50), (12, 2), (12, 22), 3)
        return surf
    
    # Fallback générique
    surf = pygame.Surface((22, 22), pygame.SRCALPHA)
    pygame.draw.circle(surf, (120, 120, 120), (11, 11), 10)
    return surf


def charger_animation_ui(dossier: str, pattern_fichier: str = "*.png", scale: float = 1.0) -> list[pygame.Surface]:
    """
    Charge une animation d'interface utilisateur depuis plusieurs fichiers séparés.
    
    Args:
        dossier: Dossier dans assets (ex: 'heart')
        pattern_fichier: Pattern de nom de fichier (ex: '*.png')
        scale: Facteur d'échelle
    
    Returns:
        Liste des surfaces pygame triées par nom de fichier
    """
    frames = []
    chemin_dossier = os.path.join(ASSETS_DIR, dossier)
    
    if not os.path.isdir(chemin_dossier):
        return frames
    
    fichiers = [f for f in os.listdir(chemin_dossier) if f.lower().endswith(".png")]
    if not fichiers:
        return frames
    
    fichiers.sort()
    
    for fichier in fichiers:
        chemin_fichier = os.path.join(chemin_dossier, fichier)
        try:
            img = pygame.image.load(chemin_fichier).convert_alpha()
            if scale != 1.0:
                img = pygame.transform.scale(
                    img, 
                    (int(img.get_width() * scale), int(img.get_height() * scale))
                )
            frames.append(img)
        except Exception:
            continue
    
    return frames


def charger_spritesheet_ui(chemin_fichier: str, nb_frames: int, scale: float = 1.0) -> list[pygame.Surface]:
    """
    Charge une spritesheet d'interface utilisateur (un seul fichier avec plusieurs frames).
    
    Args:
        chemin_fichier: Chemin complet vers le fichier spritesheet
        nb_frames: Nombre de frames à découper
        scale: Facteur d'échelle
    
    Returns:
        Liste des surfaces pygame découpées et redimensionnées
    """
    if not os.path.exists(chemin_fichier):
        return []
    
    try:
        img = pygame.image.load(chemin_fichier).convert_alpha()
        frames = decouper_sprite(img, nb_frames, horizontal=True, copy=True)
        if scale != 1.0:
            frames = [pygame.transform.scale(
                f, 
                (int(f.get_width() * scale), int(f.get_height() * scale))
            ) for f in frames]
        return frames
    except Exception:
        return []


def charger_sprites_tour_assets(type_tour: str) -> dict:
    """
    Charge tous les assets d'une tour (frames + icône) de manière uniforme.
    
    Args:
        type_tour: Type de tour (ex: 'archer', 'catapulte', 'mage', 'campement')
    
    Returns:
        Dictionnaire avec 'frames' et 'icon'
    """
    tour_folder = os.path.join(ASSETS_DIR, "tower", type_tour)
    if not os.path.isdir(tour_folder):
        return {"frames": [], "icon": None}

    chemins = [f for f in os.listdir(tour_folder) if f.endswith(".png")]
    if not chemins:
        return {"frames": [], "icon": None}

    chemins.sort()
    dernier_chemin = os.path.join(tour_folder, chemins[-1])
    image = pygame.image.load(dernier_chemin).convert_alpha()
    
    # Découpage selon le type de tour
    if type_tour == "campement":
        slices = decouper_sprite(image, 6, horizontal=True, copy=False)
        frames = [slices]
        icon = pygame.transform.smoothscale(slices[0], (48, 48))
    else:
        # Cas tour classique : découpe en 4
        slices = decouper_sprite(image, 4, horizontal=True, copy=False)
        frames = [slices]
        icon = pygame.transform.smoothscale(slices[2], (48, 48))

    return {"frames": frames, "icon": icon}


def charger_image_simple(chemin_relatif: str, convert_alpha: bool = True) -> pygame.Surface | None:
    """
    Charge une image simple avec gestion d'erreur.
    
    Args:
        chemin_relatif: Chemin relatif vers l'image
        convert_alpha: Si True, utilise convert_alpha(), sinon convert()
    
    Returns:
        Surface pygame ou None si erreur
    """
    chemin_complet = os.path.join(PROJECT_ROOT, chemin_relatif)
    if not os.path.exists(chemin_complet):
        return None
    
    try:
        if convert_alpha:
            return pygame.image.load(chemin_complet).convert_alpha()
        else:
            return pygame.image.load(chemin_complet).convert()
    except Exception:
        return None


def charger_image_assets(nom_fichier: str, dossier: str = "", convert_alpha: bool = True) -> pygame.Surface | None:
    """
    Charge une image depuis le dossier assets.
    
    Args:
        nom_fichier: Nom du fichier image
        dossier: Sous-dossier dans assets (optionnel)
        convert_alpha: Si True, utilise convert_alpha(), sinon convert()
    
    Returns:
        Surface pygame ou None si erreur
    """
    if dossier:
        chemin = os.path.join(ASSETS_DIR, dossier, nom_fichier)
    else:
        chemin = os.path.join(ASSETS_DIR, nom_fichier)
    
    return charger_image_simple(chemin, convert_alpha)


def charger_image_avec_redimensionnement(
    chemin_relatif: str, 
    nouvelle_taille: tuple[int, int] | None = None,
    convert_alpha: bool = True
) -> pygame.Surface | None:
    """
    Charge une image et la redimensionne si nécessaire.
    
    Args:
        chemin_relatif: Chemin relatif vers l'image
        nouvelle_taille: Tuple (largeur, hauteur) pour redimensionner
        convert_alpha: Si True, utilise convert_alpha(), sinon convert()
    
    Returns:
        Surface pygame redimensionnée ou None si erreur
    """
    img = charger_image_simple(chemin_relatif, convert_alpha)
    if img is None:
        return None
    
    if nouvelle_taille:
        return pygame.transform.smoothscale(img, nouvelle_taille)
    
    return img

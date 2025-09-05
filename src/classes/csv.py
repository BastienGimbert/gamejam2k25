import csv
import os

from classes.constants import PROJECT_ROOT
from classes.ennemi import Chevalier, Gobelin, Loup, Mage, Ogre, Rat

ENEMY_CLASSES = {
    1: Loup,
    2: Rat,
    3: Gobelin,
    4: Mage,
    5: Ogre,
    6: Chevalier,
}


def creer_liste_ennemis_depuis_csv(numVague=int, chemin_csv="src/data/jeu.csv") -> list:
    ennemis = []
    # Split chemin_csv into parts and join with base_dir
    chemin_csv = os.path.join(PROJECT_ROOT, *chemin_csv.split("/"))
    with open(chemin_csv, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=";")
        for row in reader:
            id_ennemi = int(row["idEnnemi"])
            vague = int(row["numVague"])
            temps = float(row["temps"])

            if vague == numVague:
                # On récupère la classe correspondante
                cls = ENEMY_CLASSES.get(id_ennemi)
                if cls is None:
                    raise ValueError(f"ID ennemi inconnu : {id_ennemi}")

                # Création de l’ennemi avec le temps d’apparition
                ennemi = cls(tempsApparition=temps)

                ennemis.append(ennemi)

    return ennemis

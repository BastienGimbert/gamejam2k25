import csv
from classes.ennemi import Gobelin, Rat, Loup, Mage, Ennemi
from classes.position import Position

def creer_liste_ennemis_depuis_csv(tour_actuel, chemin_csv="src/data/jeu.csv"):
    ennemis = []
    with open(chemin_csv, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            type_ennemi = row["type"].lower()
            id_ennemi = int(row["id"])
            #chemin = [Position(1,1)]  # Debug visuel
            vitesse = float(row["vitesse"]) 
            pointsDeVie = int(row["pointsDeVie"]) 
            degats = int(row["degats"]) 
            temps = int(row["temps"]) 
            if type_ennemi == "gobelin":
                ennemi = Gobelin(id=id_ennemi)
            elif type_ennemi == "rat":
                ennemi = Rat(id=id_ennemi)
            elif type_ennemi == "loup":
                ennemi = Loup(id=id_ennemi)
            elif type_ennemi == "mage":
                ennemi = Mage(id=id_ennemi)
            else:
                ennemi = Ennemi(
                    id=id_ennemi,
                    vitesse=vitesse,
                    pointsDeVie=pointsDeVie,
                    degats=degats ,
                    #chemin=chemin
                )
            ennemis.append(ennemi)
    return ennemis

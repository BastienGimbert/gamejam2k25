from src.position import Position
class Ennemi:
    def __init__(self, id:int ,vitesse : float, pointDeVie :int, position : Position, degat : int):
        self.id = id
        self.vitesse = vitesse
        self.pointDeVie = pointDeVie
        self.position = position
        self.degat =degat

    def apparaitre():
        pass

    def seDeplacer():
        pass

    def perdreVie(degat : int):
        pass

    def getDistance(): 
        pass       

class Tour():
    def __init__(self, type_: str, force: int, vitesseAttaque: float, position: Position, degats: int):
        self.type = type_
        self.force = force
        self.vitesseAttaque = vitesseAttaque
        self.position = position
        self.degats = degats
        self.clock = Clock()
        self.tiree = False

    @abstractmethod
    def attaquer(self, cible: Ennemi):
        pass


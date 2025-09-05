class Position:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def copy(self):
        return Position(self.x, self.y)

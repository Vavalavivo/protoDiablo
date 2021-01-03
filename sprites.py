from pygame.sprite import Sprite, Group


class Object(Sprite):
    def __init__(self):
        super().__init__()
        pass


class Player(Object):
    def __init__(self, global_pos, cell_pos):
        super().__init__()
        self.cell_pos = cell_pos

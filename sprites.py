from pygame.sprite import Sprite, Group
import pygame
import os


class Object(Sprite):
    def __init__(self, global_pos, cell_pos, *args):
        super().__init__(*args)
        self.global_pos = global_pos
        self.cell_pos = cell_pos


class Player(Object):
    def __init__(self, focus, *args):
        super().__init__(*args)
        self.image = pygame.image.load(os.path.join('player.png'))
        self.rect = self.image.get_rect()
        self.rect.x = self.global_pos[0] - focus[1] * 64
        self.rect.y = self.global_pos[1] - focus[0] * 64

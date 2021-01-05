import pygame
import os


class Object(pygame.sprite.Sprite):
    def __init__(self, global_pos, in_cell, *args):
        super().__init__(*args)
        self.global_pos = global_pos
        self.in_cell = in_cell

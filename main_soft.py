import random
import pygame
import os
import numpy as np
from time import perf_counter

from sprites import *


class PlayingBoard:
    def __init__(self, screen, map_filename, images):
        self.screen = screen
        self.map = self.load_map(map_filename)
        self.toc = self.create_toc(images)

        self.nps_group = pygame.sprite.Group()
        self.mobs_group = pygame.sprite.Group()
        self.hero = pygame.sprite.Group()

        self.focus = [10, 40]  # y_x
        self.width = 19
        self.height = 15
        self.player = Player(self.focus, [self.focus[1] * 64 + 19 * 32, self.focus[0] * 64 + 15 * 32], [10, 32],
                             self.hero)

    def load_map(self, filename):
        interim = []
        with open(filename, 'r') as file:
            interim = [i.rstrip('\n') for i in file.readlines()]

        output = np.zeros((30, 100), dtype=int)
        for y, mas in enumerate(interim):
            for x, mark in enumerate(mas):
                if mark != '_':
                    output[y, x] = int(mark)

        return output

    def create_toc(self, images):
        output = {}

        for name in images:
            image = pygame.image.load(os.path.join(name))
            name = name.rstrip('.png')
            output[int(name.split('_')[-1])] = image

        space = pygame.Surface((64, 64))
        pygame.draw.rect(space, (0, 0, 255), pygame.Rect(0, 0, 64, 64))
        output[0] = space

        return output

    def render(self):
        yd, xd = self.focus
        area = pygame.sprite.Group()
        for y in range(-1, self.height + 1):
            for x in range(-1, self.width + 1):
                sprite = pygame.sprite.Sprite()
                sprite.image = self.toc[self.map[y + yd, x + xd]]
                sprite.rect = sprite.image.get_rect()
                sprite.rect.x = x * 64 + (32 - self.player.cell_pos[0])
                sprite.rect.y = y * 64 + (32 - self.player.cell_pos[1])
                area.add(sprite)

        area.draw(self.screen)
        self.mobs_group.draw(self.screen)
        self.nps_group.draw(self.screen)
        self.hero.draw(self.screen)


class Camera:
    def __init__(self, screen):
        self.group = pygame.sprite.Group()
        self.screen = screen
        self.mouse_pos = (0, 0)  # x_y
        self.cursor = pygame.sprite.Sprite(self.group)
        self.cursor.image = pygame.image.load(os.path.join('cursor.png'))
        self.cursor.rect = self.cursor.image.get_rect()
        self.cursor.rect.x = 0
        self.cursor.rect.y = 0

    def update_mouse(self, pos):
        self.mouse_pos = pos
        self.cursor.rect.x = pos[0]
        self.cursor.rect.y = pos[1]

    def draw(self):
        if pygame.mouse.get_focused():
            self.group.draw(self.screen)


def main():
    pygame.init()
    size = width, height = 1216, 960
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('protoDiablo')
    pygame.mouse.set_visible(False)

    FPS = 30
    board = PlayingBoard(screen, 'map.txt', ('sprite_1.png',))
    camera = Camera(screen)
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEMOTION:
                mouse_pos = event.pos
                camera.update_mouse(mouse_pos)

        screen.fill((0, 255, 0))
        board.render()
        camera.draw()
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == '__main__':
    main()

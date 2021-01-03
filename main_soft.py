import random
import pygame
import os

from sprites import *


class PlayingBoard:
    space = pygame.sprite.Sprite()
    space.image = pygame.Surface((64, 64))
    pygame.draw.rect(space.image, (0, 0, 0), pygame.Rect(0, 0, 64, 64))
    space.rect = space.image.get_rect()

    grow = pygame.sprite.Sprite()
    grow.image = pygame.image.load(os.path.join('sprite_1.png'))
    grow.rect = grow.image.get_rect()
    TOC = {
        '_': space,
        '1': grow
    }

    def __init__(self, screen, filename):
        self.screen = screen
        self.map = self.load_map(filename)
        self.focus = [10, 11]  # y_x
        self.width = 19
        self.height = 15
        self.player = Player(global_pos=[640 + 19 * 32, 640 + 15 * 32], cell_pos=[0, 32])

    def load_map(self, filename):
        output = []
        with open(filename, 'r') as file:
            output = [i.rstrip('\n') for i in file.readlines()]
        return output

    def render(self):
        yd, xd = self.focus
        area = pygame.sprite.Group()
        for y in range(-1, self.height + 1):
            for x in range(-1, self.width + 1):
                if self.map[y + yd][x + xd] == '1':
                    grow = pygame.sprite.Sprite()
                    grow.image = pygame.image.load(os.path.join('sprite_1.png'))
                    grow.rect = grow.image.get_rect()
                    sprite = grow
                else:
                    space = pygame.sprite.Sprite()
                    space.image = pygame.Surface((64, 64))
                    pygame.draw.rect(space.image, (0, 0, 0), pygame.Rect(0, 0, 64, 64))
                    space.rect = space.image.get_rect()
                    sprite = space
                sprite.rect.x = x * 64 + (32 - self.player.cell_pos[0])
                sprite.rect.y = y * 64 + (32 - self.player.cell_pos[1])
                area.add(sprite)

        area.draw(self.screen)


def main():
    pygame.init()
    size = width, height = 1216, 960
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('protoDiablo')

    FPS = 30
    board = PlayingBoard(screen, 'map.txt')
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 255, 0))
        board.render()
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == '__main__':
    main()

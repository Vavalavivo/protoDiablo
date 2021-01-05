import random
import pygame
import os
import numpy as np
import states
import sprites

from time import perf_counter


class PlayingBoard:
    def __init__(self, screen, running, map_filename, images, fps):
        self.screen = screen
        self.running = running
        self.fps = fps
        self.camera = None
        self.cursor = None
        self.map = self.load_map(map_filename)
        self.toc = self.create_toc(images)
        self.cell_size = np.array([64, 128], int)  # height_width
        self.cell_width = 128
        self.cell_height = 64

        self.nps_group = pygame.sprite.Group()
        self.mobs_group = pygame.sprite.Group()
        self.hero = pygame.sprite.Group()

        self.width = 9
        self.height = 11
        self.win_width = self.width * self.cell_width
        self.win_height = self.height * self.cell_height
        self.player = Player(self)

        self.attacks = {}

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
            try:
                image = pygame.image.load(os.path.join('data_images', name))
            except Exception as exc:
                self.running[0] = False
                return
            name = name.rstrip('.png')
            if '_' in name:
                output[int(name.split('_')[-1])] = image
            else:
                output[name] = image

        space = pygame.Surface((128, 64))
        pygame.draw.rect(space, (0, 0, 255), pygame.Rect(0, 0, 128, 64))
        output[0] = output['rock']

        return output

    def set_ref(self, cursor):
        self.cursor = cursor

    def get_attacks(self):
        return self.attacks

    def clicked(self):  # !!! Определить ПОНОВОЙ
        x1, y1 = self.player.sprite.rect.x // self.cell_width, self.player.sprite.rect.y // self.cell_height
        mp = self.cursor.get_pos()
        x2 = (mp[0] - (self.cell_width // 2 - self.player.in_cell[0]) + 32) // self.cell_width
        y2 = (mp[1] - (self.cell_height // 2 - self.player.in_cell[1]) - 32) // self.cell_height

        path = self.has_path(x1, y1, x2, y2)
        if not path:
            return

        path = path + self.player.focus

        self.player.state = states.Moving(path, self.player)

    def get_cell(self, global_pos):
        output = np.array([global_pos[0] % self.cell_height,
                           global_pos[1] % self.cell_width], int)

        return output

    def has_path(self, x1, y1, x2, y2):
        d = {(x1, y1): []}
        v = [(x1, y1)]
        map = np.zeros((self.height, self.width), dtype=int)
        for y in range(self.height):
            for x in range(self.width):
                map[y, x] = self.map[y + self.player.focus[0], x + self.player.focus[1]]
        while len(v) > 0 and (x2, y2) not in d:
            x, y = v.pop(0)
            for yd in range(-1, 2):
                for xd in range(-1, 2):
                    if self.width <= x + xd or x + xd < 0 or self.height <= y + yd or y + yd < 0 or \
                            x + 1 >= self.width or x - 1 < 0 or y + 1 >= self.height or y - 1 < 0:
                        continue
                    if xd in (-1, 1) and yd != 0 and 0 in (map[y, 1 + x], map[y, -1 + x]) or \
                            yd in (-1, 1) and xd != 0 and 0 in (map[1 + y, x], map[-1 + y, x]):
                        continue
                    if map[y + yd, x + xd] != 0:
                        tr = d.get((x + xd, y + yd), -1)
                        if tr == -1:
                            d[(x + xd, y + yd)] = d[(x, y)] + [(y + yd, x + xd)]  # y_x т.к. в self.map y_x
                            v.append((x + xd, y + yd))

        return d.get((x2, y2), [])

    def render(self):
        self.player.update()
        yd, xd = self.player.focus[0], self.player.focus[1]
        area = pygame.sprite.Group()

        for y in range(-1, self.height + 1):
            for x in range(-1, self.width + 1):
                sprite = pygame.sprite.Sprite()
                sprite.image = self.toc[self.map[y + yd, x + xd]]
                sprite.rect = sprite.image.get_rect()
                sprite.rect.x = x * self.cell_width + (self.cell_width // 2 - self.player.in_cell[1])
                sprite.rect.y = y * self.cell_height + (self.cell_height // 2 - self.player.in_cell[0])
                area.add(sprite)

        area.draw(self.screen)

        self.mobs_group.draw(self.screen)

        self.nps_group.draw(self.screen)

        self.player.draw(self.screen)


class Player:
    def __init__(self, board):
        self.global_pos = np.array([540, 2000], int)
        self.board = board

        self.in_cell = np.array([self.global_pos[0] % self.board.cell_height,
                                 self.global_pos[1] % self.board.cell_width], int)  # y_x

        # y_x, показывает с какой КЛЕТКИ ПОЛЯ камера показывает картинку
        self.focus = np.array([(self.global_pos[0] - self.board.win_height // 2 -
                                self.in_cell[0]) // self.board.cell_height + 1,
                               (self.global_pos[1] - self.board.win_width // 2 -
                                self.in_cell[1]) // self.board.cell_width + 1], int)

        self.state = states.Stay(self)

        self.hp = 100
        self.speed = 15  # p/frame

        self.sprite_group = pygame.sprite.Group()
        self.sprite = pygame.sprite.Sprite(self.sprite_group)
        self.sprite.image = board.toc['player']
        self.sprite.rect = self.sprite.image.get_rect()
        self.sprite.rect.x = self.board.win_width // 2 - 32
        self.sprite.rect.y = self.board.win_height // 2 - 32

    def draw(self, screen):
        self.sprite_group.draw(screen)

    def update(self):
        for mob, info in self.board.attacks.items():
            if info[0] == 'PLAYER':
                self.hp -= info[1]
                self.board.attacks.pop(mob)
                # DEATH!!!

        if self.state.do():
            self.in_cell = np.array([self.global_pos[0] % self.board.cell_height,
                                     self.global_pos[1] % self.board.cell_width], int)

            self.focus = np.array([(self.global_pos[0] - self.board.win_height // 2 -
                                    self.in_cell[0]) // self.board.cell_height + 1,
                                   (self.global_pos[1] - self.board.win_width // 2 -
                                    self.in_cell[1]) // self.board.cell_width + 1], int)


class Cursor:
    def __init__(self, screen, running, board):
        self.screen = screen
        self.running = running

        self.group = pygame.sprite.Group()
        self.sprite = pygame.sprite.Sprite(self.group)

        self.sprite.image = board.toc['cursor']
        self.sprite.rect = self.sprite.image.get_rect()
        self.sprite.rect.x = 0
        self.sprite.rect.y = 0

    def update_pos(self, pos):
        self.sprite.rect.x = pos[0]
        self.sprite.rect.y = pos[1]

    def get_pos(self):
        return self.sprite.rect.x, self.sprite.rect.y

    def draw(self):
        if pygame.mouse.get_focused():
            self.group.draw(self.screen)


def main():
    pygame.init()
    size = width, height = 1152, 704
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('protoDiablo')
    pygame.mouse.set_visible(False)

    FPS = 30
    running = [True]
    images = (
        'sprite_1.png',
        'player.png',
        'cursor.png',
        'rock.png'
    )
    board = PlayingBoard(screen, running, 'map.txt', images, FPS)
    if not running[0]:
        return
    cursor = Cursor(screen, running, board)
    board.set_ref(cursor)
    clock = pygame.time.Clock()

    while running[0]:
        st = perf_counter()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running[0] = False
            if event.type == pygame.MOUSEMOTION:
                cursor.update_pos(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN:
                board.clicked()

        screen.fill((0, 255, 0))
        board.render()
        cursor.draw()
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == '__main__':
    main()

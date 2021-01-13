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

        self.out_view = pygame.sprite.Group()
        self.in_view = pygame.sprite.Group()
        self.mobs_points = [sprites.MobsGroup(np.array([600, 2300], int))]

        self.width = 9
        self.height = 11
        self.win_width = self.width * self.cell_width
        self.win_height = self.height * self.cell_height

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
                print('ЧТО-ТО НЕ ТАК С ИЗОБРАЖЕНИЯМИ')
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

    def set_ref(self, cursor, player):
        self.cursor = cursor
        self.player = player
        self.out_view.add(self.player)

    def create_mobs(self, point):
        for _ in range(random.randint(1, 3)):
            pos = np.array([random.randint(point.global_pos[0] - 256, point.global_pos[0] + 256),
                            random.randint(point.global_pos[1] - 256, point.global_pos[1] + 256)], int)
            spt = sprites.Mob(pos, self)
            point.add(spt)
            self.out_view.add(spt)

    def set_attack(self, start, end):
        if start not in self.attacks:
            self.attacks[start] = [(end, start.damage)]
            return
        self.attacks[start].append((end, start.damage))

    def get_attacks(self):
        return self.attacks

    def clicked(self):  # !!! Определить ПОНОВОЙ
        x1, y1 = self.win_width // 2 // self.cell_width, self.win_height // 2 // self.cell_height
        mp = self.cursor.get_pos()
        x2 = (mp[0] - (self.cell_width // 2 - self.player.in_cell[0]) + 32) // self.cell_width
        y2 = (mp[1] - (self.cell_height // 2 - self.player.in_cell[1]) - 32) // self.cell_height

        path = self.has_path(x1, y1, x2, y2)
        if not path:
            return

        path = path + self.player.focus

        self.player.set_states(states.Moving(path, self.player))

    def get_cell(self, global_pos):
        output = np.array([global_pos[0] % self.cell_height,
                           global_pos[1] % self.cell_width], int)

        return output

    def get_line(self, start, end):
        vector = end - start
        return np.sum(vector * vector) ** 0.5

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
        self.in_view.empty()
        self.out_view.update()

        for group in self.mobs_points:
            line = self.get_line(self.player.global_pos, group.global_pos)
            if not group.sprites():
                if line <= 2000:
                    self.create_mobs(group)
            else:
                if line >= 3000:
                    [i.kill() for i in group.sprites()]

        pre_sort = []
        for sprite in self.out_view.sprites():
            if self.get_line(self.player.global_pos, sprite.global_pos) <= 1500:
                pre_sort.append(sprite)
        pre_sort.sort(key=lambda ob: ob.rect.y)

        [self.in_view.add(i) for i in pre_sort]
        self.in_view.add(self.player)

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

        self.in_view.draw(self.screen)


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
    player = sprites.Player(np.array([540, 2000], int), board)
    board.set_ref(cursor, player)
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

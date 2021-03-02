import random
import pygame
import os
import numpy as np
import states
import sprites

from math import pi, acos

from time import perf_counter


class PlayingBoard:
    def __init__(self, screen, running, map_filename, fps):
        self.screen = screen
        self.running = running
        self.fps = fps
        self.camera = None
        self.cursor = None
        self.player = None
        self.map = self.load_map(map_filename)
        self.toc = self.create_toc()
        self.cell_size = np.array([64, 128], int)  # height_width
        self.cell_width = 128
        self.cell_height = 64

        self.out_view = pygame.sprite.Group()
        self.in_view = pygame.sprite.Group()
        self.effects = pygame.sprite.Group()
        self.mobs_points = [sprites.MobsGroup(np.array([1000, 2500], int)),
                            sprites.MobsGroup(np.array([1800, 2000], int)),
                            sprites.MobsGroup(np.array([1300, 3000], int)),
                            sprites.MobsGroup(np.array([540, 1700], int))]

        self.width = 9
        self.height = 11
        self.win_width = self.width * self.cell_width
        self.win_height = self.height * self.cell_height

        self.attacks = {}

    def load_map(self, filename):
        interim = []
        with open(filename, 'r') as file:
            interim = [i.rstrip('\n').split() for i in file.readlines()]

        output = np.zeros((50, 100), dtype=int)
        for y, mas in enumerate(interim):
            for x, mark in enumerate(mas):
                if mark != '_':
                    output[y, x] = int(mark)

        return output

    def create_toc(self):
        output = {}

        try:
            for name in os.listdir(r'data_images\ground'):
                tags = name.rstrip('.png').split('_')
                output[int(tags[1])] = pygame.image.load(os.path.join(r'data_images\ground', name))
        except Exception as exc:
            print('ЧТО-ТО НЕ ТАК С ИЗОБРАЖЕНИЯМИ')
            raise exc

        return output

    def set_ref(self, cursor, player):
        self.cursor = cursor
        self.player = player
        self.out_view.add(self.player)
        [self.create_mobs(gr) for gr in self.mobs_points]

    def create_mobs(self, point):
        for _ in range(random.randint(1, 5)):
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

        move = True
        for sprite in self.in_view.sprites():
            if sprite.rect.collidepoint(mp) and sprite != self.player:
                if self.player.states[0].text == 'attack':
                    move = False
                    break
                if self.get_line(self.player.global_pos, sprite.global_pos) <= 128 and self.player.cdn == 0:
                    self.player.set_states(states.Attack(sprite, self.player))
                    move = False
                    break
                elif self.get_line(self.player.global_pos, sprite.global_pos) <= 128 and self.player.cdn != 0:
                    move = False
                    break

        if not move:
            vector = np.array([mp[1], mp[0]]) + self.player.focus * self.cell_size - self.player.global_pos
            line = np.sum(vector * vector) ** 0.5
            if vector[0] >= 0:
                angle = acos(vector[1] / line)
            else:
                angle = 2 * pi - acos(vector[1] / line)

            if pi / 2 < angle <= 3 * pi / 2:
                self.player.orientation = 1
            else:
                self.player.orientation = 0
            return

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
                    if map[y + yd, x + xd] // 10 != 8 and map[y + yd, x + xd] // 10 != 9:
                        tr = d.get((x + xd, y + yd), -1)
                        if tr == -1:
                            d[(x + xd, y + yd)] = d[(x, y)] + [(y + yd, x + xd)]  # y_x т.к. в self.map y_x
                            v.append((x + xd, y + yd))

        return d.get((x2, y2), [])

    def render(self):
        self.in_view.empty()

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

        self.out_view.update()
        keys = [i for i in self.attacks]
        for key in keys:
            value = self.attacks.pop(key)
            for sprite, damage in value:
                flag = sprite.hp == sprite.full
                sprite.takes_damage(damage)
                dmg = sprites.EfDamaged(sprite.global_pos.copy(), self)
                if sprite != self.player and flag:
                    hp = sprites.EfHp(sprite, sprite.global_pos.copy(), self, (self.effects, self.out_view))
                self.effects.add(dmg)
                self.out_view.add(dmg)

        self.effects.draw(self.screen)

        for n, gr in enumerate(self.mobs_points):
            if not gr.sprites():
                _ = self.mobs_points.pop(n)


class Interface:
    def __init__(self, screen, running, board):
        self.funcs = {
            'continue': self.continue_gm,
            'save': self.save_gm,
            'exit': self.exit,
            'none': self.nothing
        }
        self.board = board
        self.states = {'ingame': states.InGame(self.funcs, self),
                       'death': states.Death(self.funcs, self),
                       'pause': states.Pause(self.funcs, self),
                       'menu': states.Menu(self.funcs, self),
                       'dialog': states.Dialog(self.funcs, self)}

        self.running = running
        self.screen = screen
        self.active = pygame.sprite.Group()
        self.passive = pygame.sprite.Group()
        self.state = 'ingame'

        self.past_screen = self.screen.copy()

    def draw(self):
        state = self.states[self.state]
        state.set_background(self.past_screen)
        state.update()
        for key, value in state.get_environment().items():
            for sprite in value:
                if key == 'pass':
                    self.passive.add(sprite)
                else:
                    self.active.add(sprite)

        self.passive.draw(self.screen)
        self.active.draw(self.screen)

        self.passive.empty()
        self.active.empty()

    def take_screen(self):
        self.past_screen = self.screen.copy()

    def set_state(self, state):
        self.state = state

    def clicked(self, mp):
        for sprite in self.states[self.state].sprites['act'] + self.states[self.state].sprites['pass']:
            if sprite.rect.collidepoint(mp):
                sprite.get_func()()
                return True

    def get_info(self):
        return self.board.player.get_rhp(), self.board.player.n, self.board.player.get_prg()

    def continue_gm(self):
        self.set_state('ingame')

    def save_gm(self):
        pass
        '''with open('data_player.txt', 'w') as file:
            file.write('x'.join(self.board.player.global_pos))
            file.write(self.board.player.prg)'''

    def exit(self):
        self.running[0] = False

    def nothing(self):
        pass


def main():
    pygame.init()
    size = width, height = 1152, 704
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('protoDiablo')
    pygame.mouse.set_visible(False)

    FPS = 30
    running = [True]
    board = PlayingBoard(screen, running, 'map.txt', FPS)
    if not running[0]:
        return
    cursor = sprites.Cursor(screen, running, board)
    player = sprites.Player(np.array([540, 2000], int), board)
    board.set_ref(cursor, player)
    interface = Interface(screen, running, board)
    clock = pygame.time.Clock()

    while running[0]:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running[0] = False
            if event.type == pygame.MOUSEMOTION:
                cursor.update_pos(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN:
                cursor.update('down')
                if not interface.clicked(cursor.get_pos()) and interface.state == 'ingame':
                    board.clicked()
            if event.type == pygame.MOUSEBUTTONUP:
                cursor.update('idle')
            if event.type == pygame.KEYDOWN:
                if interface.state == 'ingame':
                    if event.key == 27:
                        interface.set_state('pause')
                    elif event.key == 101:
                        board.player.heal()
                else:
                    if event.key == 27:
                        interface.set_state('ingame')

        if player.hp <= 0:
            interface.set_state('death')

        screen.fill((0, 255, 0))
        if interface.state == 'ingame':
            board.render()
            interface.take_screen()
        interface.draw()
        cursor.draw()
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == '__main__':
    main()

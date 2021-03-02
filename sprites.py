import pygame

import os

import numpy as np

import states

from math import pi, acos

import random


class Animation(list):
    def __init__(self, *args):
        super().__init__([i for i in args])
        self.timers = [int(i.rstrip('.png').split('_')[2]) for i in args]

    def append(self, object):
        super().append(object)
        self.timers.append(int(object.rstrip('.png').split('_')[2]))

    def get(self, index):
        if self.timers[index[0]] == index[1]:
            output = self[index[0]]
            if index[0] + 1 == len(self.timers):
                index[0] = 0
            else:
                index[0] += 1
            return output, lambda x: 0, index[0] == 0

        return self[index[0] - 1], lambda x: x + 1, False


data_ani_mobs = {}
try:
    for name in os.listdir(r'data_images\mob'):
        tags = name.split('_')
        if tags[0] not in data_ani_mobs:
            data_ani_mobs[tags[0]] = Animation(name)
            continue
        data_ani_mobs[tags[0]].append(name)

    for _, ant in data_ani_mobs.items():
        ant.sort(key=lambda x: int(x.rstrip('.png').split('_')[1]))
        for i in range(len(ant)):
            ant[i] = pygame.image.load(os.path.join('data_images', 'mob', ant[i]))
except Exception as exc:
    print('ЧТО-ТО НЕ ТАК С ИЗОБРАЖЕНИЯМИ')
    raise exc
else:
    if len(data_ani_mobs.keys()) != 3:
        print('ЧТО-ТО НЕ ТАК С ИЗОБРАЖЕНИЯМИ')
        raise Exception


class Object(pygame.sprite.Sprite):
    def __init__(self, global_pos, board, *args):
        super().__init__(*args)
        self.global_pos = global_pos
        self.board = board
        self.in_cell = np.array([self.global_pos[0] % self.board.cell_height,
                                 self.global_pos[1] % self.board.cell_width], int)  # y_x

        self.hp = None
        self.full = None
        self.speed = None
        self.damage = None

        self.orientation = 0
        self.index = [0, 0]
        self.data_animations = {}
        self.states = None
        self.animation = None

    def set_states(self, *states):
        self.animation = self.data_animations[states[0].text]
        self.index = [0, 0]
        self.states = [i for i in states]

    def update_image(self, x, y):
        self.rect = self.image.get_rect()
        if self.board.in_view in self.groups():
            interim = self.global_pos - self.board.player.focus * self.board.cell_size
            self.rect.x = interim[1] - x + self.board.cell_width // 2 - self.board.player.in_cell[1]
            self.rect.y = interim[0] - y + self.board.cell_height // 2 - self.board.player.in_cell[0]
            return
        self.rect.x = -200
        self.rect.y = -200

    def upline(self, *args):
        return False

    def takes_damage(self, *args):
        pass


class Mob(Object):
    def __init__(self, *args):
        super().__init__(*args)

        self.orientation = random.choice((0, 1))
        self.data_animations = data_ani_mobs

        self.hp = 80
        self.full = 80
        self.speed = 6
        self.damage = 15
        self.cdn = 0  # frames, max=60

        self.to = 0

        self.set_states(states.Standing(self))
        self.update()

    def update(self):
        self.cdn = max(0, self.cdn - 1)

        if self.states[0].do():
            self.in_cell = np.array([self.global_pos[0] % self.board.cell_height,
                                     self.global_pos[1] % self.board.cell_width], int)

        if self.orientation == 0:
            im, fun, stop = self.animation.get(self.index)
            self.image = im
            self.update_image(50, 64)
        else:
            im, fun, stop = self.animation.get(self.index)
            self.image = pygame.transform.flip(im, True, False)
            self.update_image(75, 64)

        if stop and self.states[0].text == 'attack':
            self.set_states(states.Standing(self))

        self.index[1] = fun(self.index[1])

        if self.to != 15:
            self.to += 1
            return
        else:
            self.to = 0

        # Проверка дальности до игрока
        line = self.board.get_line(self.global_pos, self.board.player.global_pos)
        vector = self.board.player.global_pos - self.global_pos
        if line <= self.rect.w:
            if self.cdn == 0 and self.states[0].text != 'attack':
                if vector[0] >= 0:
                    angle = acos(vector[1] / line)
                else:
                    angle = 2 * pi - acos(vector[1] / line)

                if pi / 2 < angle <= 3 * pi / 2:
                    self.orientation = 1
                else:
                    self.orientation = 0
                self.set_states(states.MobAttack(self.board.player, self))
            elif self.cdn != 0:
                pass
        elif line <= 300:
            x1, y1 = (self.global_pos - self.board.player.focus * self.board.cell_size - (
                    self.board.cell_size // 2 - self.board.player.in_cell) + np.array(
                [64, 64])) // self.board.cell_size
            x2 = self.board.win_width // 2 // self.board.cell_width
            y2 = self.board.win_height // 2 // self.board.cell_height
            path = self.board.has_path(x1, y1, x2, y2)
            if not path:
                pass
            else:
                path = path + self.board.player.focus
                self.set_states(states.Moving(path, self))
        elif line >= 300:
            self.set_states(states.Standing(self))

    def upline(self, path, index, line):
        return index + 1 == np.shape(path)[0] and line <= 64

    def get_rhp(self):
        return self.hp / self.full

    def takes_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.board.player.prg += 1
            self.kill()


class Player(Object):
    def __init__(self, *args):
        super().__init__(*args)

        self.focus = None
        self.update_camera()

        self.hp = 100
        self.full = self.hp
        self.prg = 0
        self.full_prg = 100
        self.n = 5
        self.speed = 10  # p/frame
        self.damage = 10
        self.cdn = 0  # max=45 frames

        try:
            for name in os.listdir(r'data_images\player'):
                tags = name.split('_')
                if tags[0] not in self.data_animations:
                    self.data_animations[tags[0]] = Animation(name)
                    continue
                self.data_animations[tags[0]].append(name)

            for _, ant in self.data_animations.items():
                ant.sort(key=lambda x: int(x.rstrip('.png').split('_')[1]))
                for i in range(len(ant)):
                    ant[i] = pygame.image.load(os.path.join('data_images', 'player', ant[i]))
        except Exception as exc:
            print('ЧТО-ТО НЕ ТАК С ИЗОБРАЖЕНИЯМИ')
            raise exc
        else:
            if len(self.data_animations.keys()) != 3:
                print('ЧТО-ТО НЕ ТАК С ИЗОБРАЖЕНИЯМИ')
                raise Exception

        self.set_states(states.Standing(self))
        self.update()

    def update(self):
        self.cdn = max(0, self.cdn - 1)

        if self.states[0].do():
            self.in_cell = np.array([self.global_pos[0] % self.board.cell_height,
                                     self.global_pos[1] % self.board.cell_width], int)

            self.update_camera()

        # Смена кадров, есть зависимость от направления взгляда персонажа
        if self.orientation == 0:
            im, fun, stop = self.animation.get(self.index)
            self.image = im
            self.update_image(32, 76)
        else:
            im, fun, stop = self.animation.get(self.index)
            self.image = pygame.transform.flip(im, True, False)
            self.update_image(96, 76)

        if stop and self.states[0].text == 'attack':
            self.set_states(states.Standing(self))
            self.cdn = 30
            return

        self.index[1] = fun(self.index[1])

    def update_image(self, x, y):
        self.rect = self.image.get_rect()
        self.rect.x = self.board.win_width // 2 - x
        self.rect.y = self.board.win_height // 2 - y

    def update_camera(self):
        self.focus = np.array([(self.global_pos[0] - self.board.win_height // 2 -
                                self.in_cell[0]) // self.board.cell_height + 1,
                               (self.global_pos[1] - self.board.win_width // 2 -
                                self.in_cell[1]) // self.board.cell_width + 1], int)

    def get_rhp(self):
        return self.hp / self.full

    def get_prg(self):
        return self.prg

    def heal(self):
        if self.n >= 1:
            self.hp = self.full
            self.n -= 1

    def takes_damage(self, damage):
        self.hp -= damage


class Cursor:
    def __init__(self, screen, running, board):
        self.screen = screen
        self.running = running

        self.group = pygame.sprite.Group()
        self.sprite = pygame.sprite.Sprite(self.group)
        self.images = {}

        try:
            for name in os.listdir(r'data_images/cursor'):
                tags = name.split('_')
                self.images[tags[0]] = pygame.image.load(os.path.join(r'data_images/cursor', name))
        except:
            print('ЧТО-ТО НЕ ТАК С ИЗОБРАЖЕНИЯМИ')
            raise exc

        self.sprite.image = self.images['idle']
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

    def update(self, flag):
        x, y = self.sprite.rect.x, self.sprite.rect.y
        self.sprite.image = self.images[flag]
        self.sprite.rect = self.sprite.image.get_rect()
        self.sprite.rect.x = x
        self.sprite.rect.y = y


class ImageInterface(pygame.sprite.Sprite):
    def __init__(self, nmb, *args):
        super().__init__(*args)
        self.do = None
        self.lvl = None
        self.nmb = nmb

    def set_level(self, lvl):
        self.lvl = lvl

    def set_func(self, func):
        self.do = func

    def get_func(self):
        return self.do


class Effect(Object):
    def __init__(self, flag, *args):
        super().__init__(*args)

        try:
            for name in os.listdir(f'data_images/effects/{flag}'):
                tags = name.split('_')
                if tags[0] not in self.data_animations:
                    self.data_animations[tags[0]] = Animation(name)
                    continue
                self.data_animations[tags[0]].append(name)

            for _, ant in self.data_animations.items():
                ant.sort(key=lambda x: int(x.rstrip('.png').split('_')[1]))
                for i in range(len(ant)):
                    ant[i] = pygame.image.load(os.path.join(f'data_images/effects/{flag}', ant[i]))
        except Exception as exc:
            print('ЧТО-ТО НЕ ТАК С ИЗОБРАЖЕНИЯМИ')
            raise exc
        else:
            if len(self.data_animations.keys()) != 2:
                print('ЧТО-ТО НЕ ТАК С ИЗОБРАЖЕНИЯМИ')
                raise Exception


class EfDamaged(Effect):
    def __init__(self, *args):
        super().__init__('damaged', *args)

        self.set_states('damaged')
        self.update()

    def update(self):
        im, fun, stop = self.animation.get(self.index)
        self.image = im
        self.update_image(32, 64)

        self.index[1] = fun(self.index[1])

        if stop and self.states[0] == 'damaged':
            self.set_states('dmgdempt')
        elif stop and self.states[0] == 'dmgdempt':
            self.kill()

    def set_states(self, *states):
        self.animation = self.data_animations[states[0]]
        self.index = [0, 0]
        self.states = [i for i in states]


class EfHp(Effect):
    def __init__(self, sprite, *args):
        super().__init__('hp', *args)
        self.object = sprite

        im = pygame.Surface((100, 4))
        self.image = im
        self.update_image(50, 64)

    def update(self):
        if not self.object.groups():
            self.kill()
            return

        self.global_pos = self.object.global_pos.copy()
        up = self.object.get_rhp() // 0.1

        im = pygame.Surface((100, 4))
        for i in range(10):
            if i < up:
                pygame.draw.rect(im, (0, 200, 0), (10 * i, 0, 10, 4))
            else:
                pygame.draw.rect(im, (200, 0, 0), (10 * i, 0, 10, 4))

        self.image = im
        self.update_image(50, 64)


class MobsGroup(pygame.sprite.Group):
    def __init__(self, pos, *args):
        super().__init__(*args)
        self.global_pos = pos

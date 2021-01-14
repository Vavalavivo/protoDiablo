import pygame

import os

import numpy as np

import states


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


class Damaged(Object):
    pass


class Mob(Object):
    def __init__(self, *args):
        super().__init__(*args)

        self.data_animations = data_ani_mobs

        self.hp = 80
        self.speed = 6
        self.damage = 15

        self.set_states(states.Standing(self))
        self.update()

    def update(self):
        if self.states[0].do():
            self.in_cell = np.array([self.global_pos[0] % self.board.cell_height,
                                     self.global_pos[1] % self.board.cell_width], int)

        if self.orientation == 0:
            im, fun, _ = self.animation.get(self.index)
            self.image = im
            self.update_image(32, 76)
        else:
            im, fun, _ = self.animation.get(self.index)
            self.image = pygame.transform.flip(im, True, False)
            self.update_image(96, 76)

        self.index[1] = fun(self.index[1])

        line = self.board.get_line(self.global_pos, self.board.player.global_pos)
        if line <= self.rect.w / 2:
            self.set_states(states.Attack(self.board.player, self))
        elif line <= 300:
            x1, y1 = (self.global_pos - self.board.player.focus * self.board.cell_size) // self.board.cell_size
            x2 = self.board.win_width // 2 // self.board.cell_width
            y2 = self.board.win_height // 2 // self.board.cell_height
            path = self.board.has_path(x1, y1, x2, y2)
            if not path:
                pass
            else:
                self.set_states(states.Moving(path, self))
        elif line >= 300:
            self.set_states(states.Standing(self))

    def update_image(self, x, y):
        self.rect = self.image.get_rect()
        if self.board.in_view in self.groups():
            interim = self.global_pos - self.board.player.focus * self.board.cell_size
            self.rect.x = interim[1] - x + self.board.cell_width // 2 - self.board.player.in_cell[1]
            self.rect.y = interim[0] - y + self.board.cell_height // 2 - self.board.player.in_cell[0]
            return
        self.rect.x = -200
        self.rect.y = -200

    def takes_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.kill()


class Player(Object):
    def __init__(self, *args):
        super().__init__(*args)

        self.focus = None
        self.update_camera()

        self.hp = 100
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
            self.cdn = 20
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

    def takes_damage(self, damage):
        self.hp -= damage


class MobsGroup(pygame.sprite.Group):
    def __init__(self, pos, *args):
        super().__init__(*args)
        self.global_pos = pos

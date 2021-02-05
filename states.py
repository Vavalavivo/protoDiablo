import pygame
import numpy as np

from math import acos, pi, sin, cos

import os


class State:
    def __init__(self, other):
        self.clock = pygame.time.Clock()
        self.object = other

    def do(self, *args):
        return False


class Standing(State):
    def __init__(self, *args):
        super().__init__(*args)
        self.text = 'standing'

    pass


class Attack(State):
    def __init__(self, target, *args):  # Два класса
        super().__init__(*args)
        self.target = target
        self.text = 'attack'

    def do(self):
        # Достигнута ли середина анимации (момент нанесения удара)
        if self.object.index[0] == len(self.object.animation) // 2:
            vector = self.target.global_pos - self.object.global_pos
            line = np.sum(vector * vector) ** 0.5
            if line <= self.object.rect.w / 3 * 2:
                self.object.board.set_attack(self.object, self.target)


class MobAttack(State):
    def __init__(self, target, *args):  # Два класса
        super().__init__(*args)
        self.target = target
        self.text = 'attack'

    def do(self):
        # Достигнута ли середина анимации (момент нанесения удара)
        if self.object.index[0] == len(self.object.animation) // 2:
            vector = self.target.global_pos - self.object.global_pos
            line = np.sum(vector * vector) ** 0.5
            if line <= self.object.rect.w:
                self.object.board.set_attack(self.object, self.target)
                if self.target.hp <= 0:
                    self.object.set_states(Standing(self.object))
            elif line >= 400:
                self.object.set_state(Standing(self.object))


class Moving(State):
    def __init__(self, path, *args):
        super().__init__(*args)
        self.path = path.copy()
        self.target = 0  # Индекс точки из массива PATH
        self.center = np.array([self.object.board.cell_height // 2,
                                self.object.board.cell_width // 2], int)
        self.text = 'moving'

    def do(self):
        time = self.clock.tick() // self.object.board.fps
        speed = self.object.speed

        start = self.object.global_pos
        end = self.path[self.target] * self.object.board.cell_size + self.center  # Глобальная поз клетки

        # y1 - y2 т.к. перевернутый Y в системе координат
        vector = np.array([start[0] - end[0], end[1] - start[1]], int)
        line = np.sum(vector * vector) ** 0.5  # Рассторяние до цели
        if line <= 10:  # Достижение опр клетки в пути
            self.target += 1
            if self.target == np.shape(self.path)[0]:
                _ = self.object.states.pop(0)
                if not self.object.states:
                    self.object.set_states(Standing(self.object))
            return True

        if vector[0] >= 0:
            angle = acos(vector[1] / line)
        else:
            angle = 2 * pi - acos(vector[1] / line)

        if pi / 2 < angle <= 3 * pi / 2:
            self.object.orientation = 1
        else:
            self.object.orientation = 0

        output = np.array([int(time * speed * -sin(angle)), int(time * speed * cos(angle))])
        self.object.global_pos = self.object.global_pos + output

        return True


class StInter:
    def __init__(self, state):
        self.sprites = []
        interim = []
        try:
            for name in os.listdir(r'data_images/interface'):
                tags = name.split('_')
                if tags[0] == state:
                    interim.append(name)
        except Exception as exc:
            print('ЧТО-ТО НЕ ТАК С ИЗОБРАЖЕНИЯМИ')
            raise exc
        interim.sort(key=lambda obj: int(obj.rstrip('.png').split('_')[-1]))
        for name in interim:
            x, y = tuple(map(int, name.rstrip('.png').split('_')[-2].split('x')))
            sprite = pygame.sprite.Sprite()
            sprite.image = pygame.image.load(os.path.join(r'data_images/interface', name))
            sprite.rect = sprite.image.get_rect()
            sprite.rect.x = x
            sprite.rect.y = y
            self.sprites.append(sprite)

    def get_environment(self):
        pass


class InGame(StInter):
    def __init__(self):
        super().__init__('ingame')
        self.text = 'ingame'

    def get_hp(self, dlt):
        pass


class Pause(StInter):
    def __init__(self):
        super().__init__('pause')


class Menu(StInter):
    def __init__(self):
        super().__init__('menu')


class Dialog(StInter):
    def __init__(self):
        super().__init__('dialog')

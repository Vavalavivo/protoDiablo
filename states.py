import pygame
import numpy as np

from math import acos, pi, sin, cos


class State:
    def __init__(self, other):
        self.clock = pygame.time.Clock()
        self.object = other

    def do(self, *args):
        return False


class Stay(State):
    pass


class Moving(State):
    def __init__(self, path, *args):
        super().__init__(*args)
        self.path = path.copy()
        self.target = 0  # Индекс точки из массива PATH
        self.center = np.array([self.object.board.cell_height // 2,
                                self.object.board.cell_width // 2], int)

    def do(self):
        time = self.clock.tick() // self.object.board.fps
        speed = self.object.speed

        start = self.object.global_pos
        end = self.path[self.target] * self.object.board.cell_size + self.center  # Глобальная поз клетки

        # y1 - y2 т.к. перевернутый Y в системе координат
        vector = np.array([start[0] - end[0], end[1] - start[1]], int)
        line = np.sum(vector * vector) ** 0.5  # Рассторяние до цели
        if line <= 10:  # Достижение опр клетки в пути
            # self.object.global_pos = end
            self.target += 1
            if self.target == np.shape(self.path)[0]:
                self.object.state = Stay(self.object)
            return True

        if vector[0] >= 0:
            angle = acos(vector[1] / line)
        else:
            angle = 2 * pi - acos(vector[1] / line)

        output = np.array([int(time * speed * -sin(angle)), int(time * speed * cos(angle))])
        self.object.global_pos = self.object.global_pos + output

        return True
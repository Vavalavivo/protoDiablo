import pygame
import numpy as np
import os
import sprites

from math import acos, pi, sin, cos


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


class Attack(State):
    def __init__(self, target, *args):  # Два класса
        super().__init__(*args)
        self.target = target
        self.text = 'attack'

    def do(self):
        # Достигнута ли середина анимации (момент нанесения удара)
        if self.object.index[0] == len(self.object.animation) // 2 and self.object.index[1] == 0:
            vector = self.target.global_pos - self.object.global_pos
            line = np.sum(vector * vector) ** 0.5
            if line <= self.object.rect.w:
                self.object.board.set_attack(self.object, self.target)


class MobAttack(State):
    def __init__(self, target, *args):  # Два класса
        super().__init__(*args)
        self.target = target
        self.text = 'attack'

    def do(self):
        # Достигнута ли середина анимации (момент нанесения удара)
        if self.object.index[0] == len(self.object.animation) // 2 and self.object.index[1] == 0:
            vector = self.target.global_pos - self.object.global_pos
            line = np.sum(vector * vector) ** 0.5
            if line <= self.object.rect.w:
                self.object.board.set_attack(self.object, self.target)
                self.object.cdn = 60
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
        time = 1
        speed = self.object.speed

        start = self.object.global_pos
        end = self.path[self.target] * self.object.board.cell_size + self.center  # Глобальная поз клетки

        # y1 - y2 т.к. перевернутый Y в системе координат
        vector = np.array([start[0] - end[0], end[1] - start[1]], int)
        line = np.sum(vector * vector) ** 0.5  # Рассторяние до цели
        if line <= 20 or self.object.upline(self.path, self.target, line):  # Достижение опр клетки в пути
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
    def __init__(self, state, funcs, object):
        spr = sprites.ImageInterface('999')
        spr.set_level(0)
        spr.image = pygame.Surface((10, 10))
        spr.rect = spr.image.get_rect()
        spr.rect.x = 0
        spr.rect.y = 0
        self.sprites = {
            'pass': [spr, ],
            'act': []
        }

        self.object = object

        self.funcs = funcs.copy()

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
            sprite = sprites.ImageInterface(name.split('_')[1])
            sprite.set_func(funcs[name.split('_')[-4]])
            sprite.set_level(int(name.rstrip('.png').split('_')[-1]))
            sprite.image = pygame.image.load(os.path.join(r'data_images/interface', name))
            sprite.rect = sprite.image.get_rect()
            sprite.rect.x = x
            sprite.rect.y = y
            if name.split('_')[-3] == 'pass':
                self.sprites['pass'].append(sprite)
            else:
                self.sprites['act'].append(sprite)

    def get_environment(self):
        return self.sprites.copy()

    def update(self):
        pass

    def clear(self):
        _ = self.sprites['pass'].pop(0)

    def set_sprite(self, surface, fun, gr, pos, lvl, nmb):
        spr = sprites.ImageInterface(nmb)
        spr.image = surface
        spr.rect = spr.image.get_rect()
        spr.rect.x = pos[0]
        spr.rect.y = pos[1]
        spr.set_func(self.funcs[fun])
        spr.set_level(lvl)
        self.sprites[gr].append(spr)

        self.sprites['pass'].sort(key=lambda ob: ob.lvl)
        self.sprites['act'].sort(key=lambda ob: ob.lvl)

    def set_background(self, *args):
        pass


class InGame(StInter):
    def __init__(self, *args):
        super().__init__('ingame', *args)
        self.text = 'ingame'

        self.update()

    def update(self):
        font_h = pygame.font.Font(None, 30)
        health = font_h.render(f'{int(self.object.get_info()[0] * 100)}%', True, (200, 30, 10))
        pos_h = (500, 656)
        scr_h = pygame.Surface((health.get_width(), health.get_height()))
        scr_h.set_colorkey((0, 0, 0))
        scr_h.blit(health, (0, 0))

        font_n = pygame.font.Font(None, 30)
        nul = font_n.render(f'{self.object.get_info()[1]}', True, (100, 63, 150))
        pos_n = (600, 656)
        scr_n = pygame.Surface((nul.get_width(), nul.get_height()))
        scr_n.set_colorkey((0, 0, 0))
        scr_n.blit(nul, (0, 0))

        font_p = pygame.font.Font(None, 30)
        prg = font_p.render(f'Монстров на ВАШЕМ счету: {self.object.get_info()[2]}', True, (189, 178, 34))
        pos_p = (450, 604)
        scr_p = pygame.Surface((prg.get_width(), prg.get_height()))
        scr_p.set_colorkey((0, 0, 0))
        scr_p.blit(prg, (0, 0))

        for i, spr in enumerate(self.sprites['pass']):
            if spr.nmb == '777' or spr.nmb == '345' or spr.nmb == '235':
                self.sprites['pass'].pop(i)

        self.set_sprite(scr_h, 'none', 'pass', pos_h, 1, '777')
        self.set_sprite(scr_p, 'none', 'pass', pos_p, 1, '345')
        self.set_sprite(scr_n, 'none', 'pass', pos_n, 1, '235')


class Pause(StInter):
    def __init__(self, *args):
        super().__init__('pause', *args)

    def set_background(self, surface):
        _ = self.sprites['pass'].pop(0)
        sprite = sprites.ImageInterface('634')
        sprite.set_func(self.funcs['none'])
        sprite.image = surface
        sprite.rect = sprite.image.get_rect()
        sprite.rect.x = 0
        sprite.rect.y = 0

        self.sprites['pass'] = [sprite] + self.sprites['pass']


class Death(StInter):
    def __init__(self, *args):
        super().__init__('death', *args)

        font = pygame.font.Font(None, 50)
        txt = font.render('YOU ARE DEAD', True, (255, 0, 0))
        face = pygame.Surface((txt.get_width(), txt.get_height()))
        face.set_colorkey((0, 0, 0))
        face.blit(txt, (0, 0))
        self.set_sprite(face, 'none', 'pass', (450, 200), 1, '898')

    def set_background(self, surface):
        _ = self.sprites['pass'].pop(0)
        sprite = sprites.ImageInterface('634')
        sprite.set_func(self.funcs['none'])
        sprite.image = surface
        sprite.rect = sprite.image.get_rect()
        sprite.rect.x = 0
        sprite.rect.y = 0

        self.sprites['pass'] = [sprite] + self.sprites['pass']


class Menu(StInter):
    def __init__(self, *args):
        super().__init__('menu', *args)
        self.clear()


class Dialog(StInter):
    def __init__(self, *args):
        super().__init__('dialog', *args)
        self.clear()

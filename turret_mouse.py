import os
import sys
import math
import pygame as pg

TURRET=None
CAPTION = "Tank Turret: Mouse"
SCREEN_SIZE = (500, 500)
#背景颜色用于提取图片中的物件
BACKGROUND_COLOR = (50, 50, 50)
COLOR_KEY = (255, 0, 255)

#炮塔类
class Turret(object):

    def __init__(self, location):
        self.original_barrel = TURRET.subsurface((0, 0, 150, 150))
        self.barrel = self.original_barrel.copy()
        self.base = TURRET.subsurface((300, 0, 150, 150))
        #pygame使用矩形控制物件的位置
        self.rect = self.barrel.get_rect(center=location)
        self.base_rect = self.rect.copy()
        self.angle = self.get_angle(pg.mouse.get_pos())
    
    #找到炮塔中心和鼠标之间的角度，参数mouse是鼠标的坐标
    def get_angle(self, mouse):
        offset = (mouse[1]-self.rect.centery, mouse[0]-self.rect.centerx)
        self.angle = 135-math.degrees(math.atan2(*offset))
        #旋转炮管
        self.barrel = pg.transform.rotate(self.original_barrel, self.angle)
        self.rect = self.barrel.get_rect(center=self.rect.center)
    #获取事件（鼠标左键或者鼠标移动）
    def get_event(self, event, objects):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            objects.add(Laser(self.rect.center, self.angle))
        elif event.type == pg.MOUSEMOTION:
            self.get_angle(event.pos)

    #在表面上画出炮架和炮管
    def draw(self, surface):
        surface.blit(self.base, self.base_rect)
        surface.blit(self.barrel, self.rect)

#激光类，继承于pygame.sprite.Sprite
class Laser(pg.sprite.Sprite):
    #通过坐标和角度进行初始化
    def __init__(self, location, angle):
        pg.sprite.Sprite.__init__(self)
        #通过坐标截取出图片中的炮弹
        self.original_laser = TURRET.subsurface((150, 0, 150, 150))
        self.angle = -math.radians(angle-135)
        self.image = pg.transform.rotate(self.original_laser, angle)
        self.rect = self.image.get_rect(center=location)
        self.move = [self.rect.x, self.rect.y]
        self.speed_magnitude = 5
        self.speed = (self.speed_magnitude*math.cos(self.angle),
                      self.speed_magnitude*math.sin(self.angle))
        self.done = False

    def update(self, screen_rect):
        self.move[0] += self.speed[0]
        self.move[1] += self.speed[1]
        self.rect.topleft = self.move
        self.remove(screen_rect)

    def remove(self, screen_rect):
        #如果炮弹移出屏幕，将其从任何group中删除
        if not self.rect.colliderect(screen_rect):
            self.kill()


class Control(object):

    def __init__(self):

        self.screen = pg.display.get_surface()
        self.screen_rect = self.screen.get_rect()
        self.done = False
        self.clock = pg.time.Clock()
        self.fps = 60.0
        self.keys = pg.key.get_pressed()
        #初始化一个炮台
        self.cannon = Turret((250, 250))
        #初始化一个列表用来存储所有炮弹
        self.objects = pg.sprite.Group()

    def event_loop(self):
        #将从鼠标获得的事件event传递给cannon
        for event in pg.event.get():
            self.keys = pg.key.get_pressed()
            if event.type == pg.QUIT or self.keys[pg.K_ESCAPE]:
                self.done = True
            self.cannon.get_event(event, self.objects)

    def update(self):
        #更新所有炮弹的状态
        self.objects.update(self.screen_rect)

    def draw(self):
        #在surface上画出炮台和所有炮弹
        self.screen.fill(BACKGROUND_COLOR)
        self.cannon.draw(self.screen)
        self.objects.draw(self.screen)

    def display_fps(self):
        #显示fps
        caption = "{} - FPS: {:.2f}".format(CAPTION, self.clock.get_fps())
        pg.display.set_caption(caption)

    def main_loop(self):
        #主循环 same old story
        while not self.done:
            self.event_loop()
            self.update()
            self.draw()
            pg.display.flip()
            self.clock.tick(self.fps)
            self.display_fps()


def run():
    global TURRET
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pg.init()
    pg.display.set_caption(CAPTION)
    pg.display.set_mode(SCREEN_SIZE)
    TURRET = pg.image.load("turret.png").convert()
    TURRET.set_colorkey(COLOR_KEY)
    run_it = Control()
    run_it.main_loop()
    pg.quit()
    sys.exit()


if __name__ == "__main__":
    run()

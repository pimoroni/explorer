"""Dice
Shake to roll.

You will need:
- Multi-Sensor Stick

Icon: casino
"""
import math
import random

import explorer
from explorer import SELECT, UP, screen
from lsm6ds3 import LSM6DS3
from picovector import color, font, image, mat3, rect, shape

screen.antialias = image.X4

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

imu = explorer.sensor(LSM6DS3, TITLE_FONT)

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
EDGE = color.rgb(196, 190, 180)
DIM = color.rgb(125, 120, 112)
SHADOW = color.rgb(0, 0, 0, 90)

ONE_G = 16384
SHAKE = 0.6 * ONE_G
SIZE = 84
GRAVITY = 1800
BOUNCE = 0.45
FLOOR_FRICTION = 2.2
SPIN_FRICTION = 2.6
REST_SPEED = 40
SETTLE = 8
FLIP_DEGREES = 70
TABLE_TOP = 40
TABLE_BOTTOM = 214
POP_MS = 400
PIPS = {
    1: ((0, 0),),
    2: ((-1, -1), (1, 1)),
    3: ((-1, -1), (0, 0), (1, 1)),
    4: ((-1, -1), (1, -1), (-1, 1), (1, 1)),
    5: ((-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)),
    6: ((-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)),
}


class Die:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.z = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.angle = 0.0
        self.spin = 0.0
        self.face = random.randint(1, 6)
        self.turned = 0.0

    def throw(self, from_left, push_x, push_y):
        self.x = -SIZE if from_left else 320 + SIZE
        self.y = random.uniform(TABLE_TOP + SIZE / 2, TABLE_BOTTOM - SIZE / 2)
        self.z = random.uniform(10, 30)
        direction = 1 if from_left else -1
        self.vx = direction * random.uniform(300, 400) + push_x
        self.vy = random.uniform(-120, 120) + push_y
        self.vz = random.uniform(200, 280)
        self.spin = direction * random.uniform(500, 900)

    def moving(self):
        return self.z > 0 or abs(self.vx) + abs(self.vy) > REST_SPEED or abs(self.spin) > REST_SPEED

    def update(self, dt):
        self.vz -= GRAVITY * dt
        self.z += self.vz * dt
        landed = False
        if self.z <= 0:
            self.z = 0.0
            if self.vz < -120:
                landed = True
                self.vz = -self.vz * BOUNCE
                self.spin *= 0.7
                self.face = random.randint(1, 6)
            else:
                self.vz = 0.0
        if self.z == 0:
            slow = max(0.0, 1 - FLOOR_FRICTION * dt)
            self.vx *= slow
            self.vy *= slow
            self.spin *= max(0.0, 1 - SPIN_FRICTION * dt)

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.spin * dt
        self.turned += abs(self.spin * dt)
        if self.turned > FLIP_DEGREES:
            self.turned = 0.0
            self.face = random.randint(1, 6)

        half = SIZE / 2
        if self.x < half and self.vx < 0:
            self.vx = -self.vx * 0.6
        if self.x > 320 - half and self.vx > 0:
            self.vx = -self.vx * 0.6
        if self.y < TABLE_TOP + half and self.vy < 0:
            self.vy = -self.vy * 0.6
        if self.y > TABLE_BOTTOM - half and self.vy > 0:
            self.vy = -self.vy * 0.6

        if not self.moving():
            self.vx = self.vy = self.spin = 0.0
            square = round(self.angle / 90) * 90
            self.angle += (square - self.angle) * min(1.0, SETTLE * dt)
        return landed

    def draw(self):
        scale = 1 + self.z / 260
        shadow = shape.rounded_rectangle(-SIZE / 2, -SIZE / 2, SIZE, SIZE, 16)
        shadow.transform = mat3().translate(self.x + 6 + self.z * 0.25, self.y + 8 + self.z * 0.15).rotate(self.angle).scale(1 / scale, 1 / scale)
        screen.pen = SHADOW
        screen.shape(shadow)

        body = mat3().translate(self.x, self.y - self.z).rotate(self.angle).scale(scale, scale)
        edge = shape.rounded_rectangle(-SIZE / 2, -SIZE / 2 + 4, SIZE, SIZE, 16)
        edge.transform = body
        screen.pen = EDGE
        screen.shape(edge)
        top = shape.rounded_rectangle(-SIZE / 2, -SIZE / 2, SIZE, SIZE - 2, 16)
        top.transform = body
        screen.pen = PAPER
        screen.shape(top)
        screen.pen = INK
        for px, py in PIPS[self.face]:
            pip = shape.circle(px * SIZE * 0.27, py * SIZE * 0.27, 8)
            pip.transform = body
            screen.shape(pip)


def collide(first, second):
    dx = second.x - first.x
    dy = second.y - first.y
    distance = math.sqrt(dx * dx + dy * dy) or 1
    if distance >= SIZE or abs(first.z - second.z) > SIZE / 2:
        return False
    nx, ny = dx / distance, dy / distance
    overlap = (SIZE - distance) / 2
    first.x -= nx * overlap
    first.y -= ny * overlap
    second.x += nx * overlap
    second.y += ny * overlap
    closing = (first.vx - second.vx) * nx + (first.vy - second.vy) * ny
    if closing > 0:
        first.vx -= closing * nx
        first.vy -= closing * ny
        second.vx += closing * nx
        second.vy += closing * ny
        first.spin, second.spin = -second.spin, -first.spin
        return True
    return False


def resting_positions(count):
    if count == 1:
        return ((160, 128),)
    return ((100, 128), (220, 128))


dice = [Die(x, y) for x, y in resting_positions(2)]
rolling = False
settled_at = explorer.ticks()
last = explorer.ticks()

while True:
    now = explorer.ticks()
    dt = min(0.05, (now - last) / 1000)
    last = now
    ax, ay, az, _, _, _ = imu.get_readings()
    shaken = abs(math.sqrt(ax * ax + ay * ay + az * az) - ONE_G) > SHAKE

    if UP.pressed and not rolling:
        dice = [Die(x, y) for x, y in resting_positions(1 if len(dice) == 2 else 2)]
    if (shaken or SELECT.pressed) and not rolling:
        rolling = True
        from_left = random.random() < 0.5
        push_x = max(-200, min(200, ax / ONE_G * 200))
        push_y = max(-200, min(200, ay / ONE_G * 200))
        for index, die in enumerate(dice):
            die.throw(from_left, push_x, push_y + (index - 0.5) * 160)

    if rolling:
        thuds = 0
        for die in dice:
            if die.update(dt):
                thuds += 1
        if len(dice) == 2 and collide(dice[0], dice[1]):
            explorer.beep(random.randint(900, 1200), 15)
        if thuds:
            explorer.beep(random.randint(140, 220), 25)
        if not any(die.moving() for die in dice):
            rolling = False
            settled_at = now
            explorer.beep(660, 40)
    else:
        for die in dice:
            die.update(dt)

    screen.pen = INK
    screen.clear()
    for die in sorted(dice, key=lambda die: die.z):
        die.draw()

    if not rolling:
        total = sum(die.face for die in dice)
        pop = min(1.0, (now - settled_at) / POP_MS)
        size = 22 + 8 * math.sin(pop * math.pi) * (1 - pop) + 4 * pop
        screen.font = TITLE_FONT
        screen.pen = PAPER
        label = f"Total {total}" if len(dice) == 2 else f"You rolled {total}"
        screen.text(label, rect(0, 6, 320, 30), size, align=(image.CENTER, image.MIDDLE))

    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text("Shake or A  Roll    X  One / two dice", 10, 222, 13)

    explorer.update()

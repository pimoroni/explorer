"""Squash
Turn the dial to keep the ball in play.

You will need:
- Potentiometer
- 3 wires

Icon: sports_tennis
"""
import random

import explorer
from explorer import ADC0, SELECT, Analog, screen, wiring
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
WALL = color.rgb(58, 56, 53)
BALL = color.rgb(255, 204, 51)

WIDTH = 320
HEIGHT = 240
COURT = 8
PADDLE_WIDTH = 60
PADDLE_Y = 220
BALL_RADIUS = 6
START_SPEED = 160
SPEED_UP = 1.06

POT_STEPS = (
    (
        "Potentiometer pins-up in columns 4, 5, 6 just above the groove, shaft over the groove",
        (wiring.potentiometer(4),),
    ),
    (
        "Wires from the left pin to GND, middle pin to ADC0, right pin to 3.3V",
        (
            wiring.wire(wiring.hole(4, 1, True), wiring.ground(5), wiring.BLACK, (60, -40), (40, 20)),
            wiring.wire(wiring.hole(5, 1, True), wiring.adc(0), (240, 200, 40), (60, -40), (40, -30)),
            wiring.wire(wiring.hole(6, 1, True), wiring.power(), wiring.RED, (60, -40), (40, -10)),
        ),
    ),
)

wiring.show(POT_STEPS, TITLE_FONT, BODY_FONT)

dial = Analog(ADC0)
paddle_x = WIDTH / 2
ball_x = ball_y = speed_x = speed_y = 0.0
score = 0
best = 0
playing = False
last = explorer.ticks()


def serve():
    global ball_x, ball_y, speed_x, speed_y
    ball_x, ball_y = WIDTH / 2, 60.0
    speed_x = random.choice((-1, 1)) * START_SPEED * 0.6
    speed_y = START_SPEED


while True:
    now = explorer.ticks()
    dt = min(50, now - last) / 1000
    last = now

    target = COURT + PADDLE_WIDTH / 2 + dial.read() * (WIDTH - 2 * COURT - PADDLE_WIDTH)
    paddle_x += (target - paddle_x) * 0.5

    if not playing and SELECT.pressed:
        playing = True
        score = 0
        serve()

    if playing:
        ball_x += speed_x * dt
        ball_y += speed_y * dt
        if ball_x < COURT + BALL_RADIUS or ball_x > WIDTH - COURT - BALL_RADIUS:
            speed_x = -speed_x
            ball_x = max(COURT + BALL_RADIUS, min(WIDTH - COURT - BALL_RADIUS, ball_x))
            explorer.beep(330, 20)
        if ball_y < COURT + BALL_RADIUS:
            speed_y = abs(speed_y)
            explorer.beep(330, 20)
        if speed_y > 0 and PADDLE_Y - BALL_RADIUS <= ball_y <= PADDLE_Y + 4 and abs(ball_x - paddle_x) < PADDLE_WIDTH / 2 + BALL_RADIUS:
            speed_y = -abs(speed_y) * SPEED_UP
            speed_x = (ball_x - paddle_x) / (PADDLE_WIDTH / 2) * abs(speed_y) * 0.8
            score += 1
            explorer.beep(660, 30)
        if ball_y > HEIGHT + BALL_RADIUS:
            playing = False
            best = max(best, score)
            explorer.beep(150, 300)

    screen.pen = INK
    screen.clear()
    screen.pen = WALL
    screen.shape(shape.rectangle(0, 0, WIDTH, COURT))
    screen.shape(shape.rectangle(0, 0, COURT, HEIGHT))
    screen.shape(shape.rectangle(WIDTH - COURT, 0, COURT, HEIGHT))

    screen.font = TITLE_FONT
    screen.pen = WALL
    screen.text(str(score), rect(0, 70, WIDTH, 80), 72, align=(image.CENTER, image.MIDDLE))

    screen.pen = PAPER
    screen.shape(shape.rounded_rectangle(paddle_x - PADDLE_WIDTH / 2, PADDLE_Y, PADDLE_WIDTH, 8, 4))
    if playing:
        screen.pen = BALL
        screen.shape(shape.circle(ball_x, ball_y, BALL_RADIUS))
    else:
        screen.font = BODY_FONT
        screen.pen = PAPER
        screen.text("A  Serve", rect(0, 150, WIDTH, 24), 18, align=(image.CENTER, image.MIDDLE))
        screen.pen = DIM
        screen.text(f"Best {best}    Dial ADC0", rect(0, 176, WIDTH, 20), 14, align=(image.CENTER, image.MIDDLE))

    explorer.update()

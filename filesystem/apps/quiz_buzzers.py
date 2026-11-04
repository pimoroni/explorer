"""Quiz Buzzers
Three players. First to buzz answers.

You will need:
- 3 switches
- 3 LEDs
- 7 wires

Icon: sports_score
"""
import explorer
from explorer import DOWN, GP0, GP1, GP2, GP3, GP4, GP5, SELECT, UP, Input, Output, screen
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)

PLAYERS = (
    ("Player 1", color.rgb(255, 122, 61), 330),
    ("Player 2", color.rgb(255, 204, 51), 440),
    ("Player 3", color.rgb(92, 150, 255), 554),
)

buzzers = (Input(GP3), Input(GP4), Input(GP5))
leds = (Output(GP0), Output(GP1), Output(GP2))
scores = [0, 0, 0]
winner = None

while True:
    if winner is None:
        for player, buzzer in enumerate(buzzers):
            if buzzer.pressed:
                winner = player
                explorer.beep(PLAYERS[player][2], 400)
                break
    else:
        if UP.pressed:
            scores[winner] += 1
            explorer.beep(880, 120)
            winner = None
        elif DOWN.pressed:
            explorer.beep(196, 200)
            winner = None
    if SELECT.pressed:
        scores = [0, 0, 0]
        winner = None

    for player, led in enumerate(leds):
        led.value(player == winner)

    screen.pen = INK if winner is None else PLAYERS[winner][1]
    screen.clear()

    screen.font = TITLE_FONT
    if winner is None:
        screen.pen = PAPER
        screen.text("Buzzers ready", rect(0, 40, 320, 60), 32, align=(image.CENTER, image.MIDDLE))
    else:
        screen.pen = INK
        screen.text(PLAYERS[winner][0], rect(0, 40, 320, 60), 40, align=(image.CENTER, image.MIDDLE))
        screen.font = BODY_FONT
        screen.text("X  Correct    Y  Wrong", rect(0, 96, 320, 24), 16, align=(image.CENTER, image.MIDDLE))

    for player, ((name, pen, _), score) in enumerate(zip(PLAYERS, scores)):
        x = 16 + player * 100
        screen.pen = FAINT if winner is None else INK
        screen.shape(shape.rounded_rectangle(x, 136, 88, 64, 12))
        screen.pen = pen
        screen.shape(shape.circle(x + 16, 152, 6))
        screen.font = BODY_FONT
        screen.pen = PAPER
        screen.text(name, x + 28, 143, 13)
        screen.font = TITLE_FONT
        screen.text(str(score), rect(x, 162, 88, 34), 28, align=(image.CENTER, image.MIDDLE))

    screen.font = BODY_FONT
    screen.pen = DIM if winner is None else INK
    screen.text("A  Reset scores    Switches GP3-GP5  LEDs GP0-GP2", 12, 220, 12)

    explorer.update()

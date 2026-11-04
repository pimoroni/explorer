"""Quiz Buzzers
Three players. First to buzz answers.

You will need:
- 3 switches
- 3 LEDs
- 7 wires

Icon: sports_score
"""
import explorer
from explorer import BACK, GP0, GP1, GP2, GP3, GP4, GP5, SELECT, Input, Output, button_y, labels, screen
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
        if SELECT.pressed:
            scores[winner] += 1
            explorer.beep(880, 120)
            winner = None
        elif BACK.pressed:
            explorer.beep(196, 200)
            winner = None
    if button_y.pressed:
        scores = [0, 0, 0]
        winner = None

    for player, led in enumerate(leds):
        led.value(player == winner)

    screen.pen = INK if winner is None else PLAYERS[winner][1]
    screen.clear()

    screen.font = TITLE_FONT
    if winner is None:
        screen.pen = PAPER
        screen.text("Buzzers ready", rect(0, 60, 320, 44), 32, align=(image.CENTER, image.MIDDLE))
    else:
        screen.pen = INK
        screen.text(PLAYERS[winner][0], rect(0, 54, 320, 56), 40, align=(image.CENTER, image.MIDDLE))

    for player, ((name, pen, _), score) in enumerate(zip(PLAYERS, scores)):
        x = 16 + player * 100
        screen.pen = FAINT if winner is None else INK
        screen.shape(shape.rounded_rectangle(x, 140, 88, 66, 12))
        screen.pen = pen
        screen.shape(shape.circle(x + 13, 156, 5))
        screen.font = BODY_FONT
        screen.pen = PAPER
        screen.text(name, x + 23, 147, 14)
        screen.font = TITLE_FONT
        screen.text(str(score), rect(x, 168, 88, 36), 30, align=(image.CENTER, image.MIDDLE))

    screen.font = BODY_FONT
    screen.pen = DIM if winner is None else INK
    screen.text("Switches GP3-GP5  LEDs GP0-GP2", rect(0, 210, 320, 30), 14, align=(image.CENTER, image.MIDDLE))

    actions = {}
    if winner is not None:
        actions["A"] = "Correct"
        actions["B"] = "Wrong"
    if winner is not None or any(scores):
        actions["Y"] = "Reset"
    labels.draw(screen, TITLE_FONT, actions)

    explorer.update()

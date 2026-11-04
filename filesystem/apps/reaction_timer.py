"""Reaction Timer
How fast can you hit the switch?

You will need:
- Green LED
- Switch
- 4 wires

Icon: timer
"""
import random

import explorer
from explorer import GP0, GP3, SELECT, Input, Output, labels, screen
from picovector import color, font, image, rect

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
GO = color.rgb(60, 200, 90)
EARLY = color.rgb(235, 60, 50)

READY, WAITING, GO_NOW, RESULT, TOO_SOON = range(5)

led = Output(GP0)
button = Input(GP3)
state = READY
go_at = 0
result = 0
best = None

while True:
    now = explorer.ticks()
    hit = button.pressed or SELECT.pressed

    if state in (READY, RESULT, TOO_SOON) and hit:
        state = WAITING
        go_at = now + random.randint(1500, 4000)
    elif state == WAITING and hit:
        state = TOO_SOON
        explorer.beep(220, 200)
    elif state == WAITING and now >= go_at:
        state = GO_NOW
        explorer.beep(880, 60)
    elif state == GO_NOW and hit:
        result = now - go_at
        best = result if best is None else min(best, result)
        state = RESULT

    led.value(state == GO_NOW)

    screen.pen = GO if state == GO_NOW else INK
    screen.clear()

    screen.font = TITLE_FONT
    screen.pen = INK if state == GO_NOW else PAPER
    if state == READY:
        message = "Press to start"
    elif state == WAITING:
        message = "Wait for it..."
    elif state == GO_NOW:
        message = "GO!"
    elif state == TOO_SOON:
        screen.pen = EARLY
        message = "Too soon!"
    else:
        message = f"{result} ms"
    screen.text(message, rect(0, 70, 320, 60), 40, align=(image.CENTER, image.MIDDLE))

    screen.font = BODY_FONT
    screen.pen = INK if state == GO_NOW else DIM
    if best is not None:
        screen.text(f"Best {best} ms", rect(0, 136, 320, 24), 18, align=(image.CENTER, image.MIDDLE))
    screen.text("LED GP0  Switch GP3", rect(0, 206, 320, 34), 14, align=(image.CENTER, image.MIDDLE))

    if state in (WAITING, GO_NOW):
        labels.draw(screen, TITLE_FONT, {"A": "Hit"}, "A" if state == GO_NOW else None)
    else:
        labels.draw(screen, TITLE_FONT, {"A": "Start" if state == READY else "Again"}, "A")

    explorer.update()

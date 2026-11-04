"""Simon
Copy the pattern. It gets longer every round.

You will need:
- Red, yellow, green LEDs
- 3 switches
- 7 wires

Icon: psychology
"""
import random

import explorer
from explorer import GP0, GP1, GP2, GP3, GP4, GP5, SELECT, Input, Output, button_x, button_y, button_z, screen
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)

PADS = (
    ((235, 60, 50), 330),
    ((255, 190, 40), 415),
    ((60, 200, 90), 494),
)
ON_MS = 400
OFF_MS = 200
FLASH_MS = 250

leds = (Output(GP0), Output(GP1), Output(GP2))
switches = (Input(GP3), Input(GP4), Input(GP5))
buttons = (button_x, button_y, button_z)

START, SHOWING, COPYING, OVER = range(4)
state = START
sequence = []
step = 0
step_at = 0
lit = None
lit_until = 0
best = 0


def light(pad, now, duration):
    global lit, lit_until
    lit = pad
    lit_until = now + duration
    explorer.beep(PADS[pad][1], duration)


while True:
    now = explorer.ticks()
    if lit is not None and now >= lit_until:
        lit = None

    pressed = None
    for pad in range(3):
        if switches[pad].pressed or buttons[pad].pressed:
            pressed = pad

    if state in (START, OVER) and SELECT.pressed:
        sequence = [random.randint(0, 2)]
        state, step, step_at = SHOWING, 0, now + 600
    elif state == SHOWING and now >= step_at:
        if step < len(sequence):
            light(sequence[step], now, ON_MS)
            step += 1
            step_at = now + ON_MS + OFF_MS
        else:
            state, step = COPYING, 0
    elif state == COPYING and pressed is not None:
        light(pressed, now, FLASH_MS)
        if pressed != sequence[step]:
            explorer.beep(110, 600)
            best = max(best, len(sequence) - 1)
            state = OVER
        else:
            step += 1
            if step == len(sequence):
                sequence.append(random.randint(0, 2))
                state, step, step_at = SHOWING, 0, now + 900

    for pad, led in enumerate(leds):
        led.value(pad == lit)

    screen.pen = INK
    screen.clear()

    for pad, ((r, g, b), _) in enumerate(PADS):
        y = 45 + pad * 74
        if pad == lit:
            screen.pen = color.rgb(r, g, b)
        else:
            screen.pen = color.rgb(r // 4, g // 4, b // 4)
        screen.shape(shape.rounded_rectangle(196, y - 30, 110, 60, 14))

    screen.font = TITLE_FONT
    screen.pen = PAPER
    if state == START:
        message = "Simon"
    elif state == SHOWING:
        message = "Watch"
    elif state == COPYING:
        message = "Your turn"
    else:
        message = "Game over"
    screen.text(message, rect(12, 60, 170, 40), 28)
    screen.font = BODY_FONT
    screen.pen = DIM
    if state != START:
        screen.text(f"Round {len(sequence)}", 12, 104, 16)
    if best:
        screen.text(f"Best {best}", 12, 126, 16)
    if state in (START, OVER):
        screen.text("A  Start", 12, 20, 14)
    screen.text("Switches GP3-5\nor X Y Z", 12, 184, 13)

    explorer.update()

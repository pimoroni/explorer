"""Flag Wave
Wave a paper flag to celebrate.

You will need:
- Servo and horn
- Paper flag
- Switch
- 2 wires

Icon: flag
"""
import math
from array import array

import explorer
from explorer import GP3, SELECT, Input, screen, wiring
from picovector import color, font, image, rect, shape
from servo import CONTINUOUS

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
POLE = color.rgb(125, 120, 112)
FLAG = color.rgb(255, 122, 61)

SERVO = 1
SPEED = 0.7
SWING_MS = 220
WAVE_MS = 2600
FANFARE = ((523, 120), (659, 120), (784, 120), (1047, 300))

WIRING = (
    ("Servo on header 1. Brown wire to GND, on the right.", (wiring.servo(SERVO),)),
    ("Button across the middle of the breadboard", (wiring.button(1),)),
    (
        "Wires from above the button to GP3 and GND",
        (
            wiring.wire(wiring.hole(1, 1, True), wiring.gpio(3), wiring.RED, (70, -10), (-70, -20)),
            wiring.wire(wiring.hole(3, 1, True), wiring.ground(5), wiring.BROWN, (70, -10), (-70, -20)),
        ),
    ),
)

wiring.show(WIRING, TITLE_FONT, BODY_FONT)

flag_servo = explorer.servo(SERVO, CONTINUOUS)
switch = Input(GP3)
waving_until = 0
waves = 0
note = 0
note_at = 0


def draw_flag(now, waving):
    screen.pen = POLE
    screen.shape(shape.rounded_rectangle(86, 30, 8, 180, 4))
    screen.shape(shape.circle(90, 30, 8))
    lean = math.sin(now / SWING_MS * math.pi) * 18 if waving else 0
    ripple = 10 if waving else 3
    top = array("f")
    bottom = array("f")
    for step in range(11):
        along = step / 10
        x = 94 + along * 150
        wave = math.sin(along * 6 - now / 120) * ripple * along
        top.extend((x, 44 + wave + lean * along))
        bottom.extend((x, 134 + wave + lean * along))
    points = array("f", top)
    for step in range(10, -1, -1):
        points.extend((bottom[step * 2], bottom[step * 2 + 1]))
    screen.pen = FLAG
    screen.shape(shape.custom(points))


while True:
    now = explorer.ticks()
    if (switch.pressed or SELECT.pressed) and now >= waving_until:
        waving_until = now + WAVE_MS
        waves += 1
        note, note_at = 0, now

    waving = now < waving_until
    if waving:
        flag_servo.value(SPEED if (now // SWING_MS) % 2 else -SPEED)
        if note < len(FANFARE) and now >= note_at:
            frequency, duration = FANFARE[note]
            explorer.beep(frequency, duration)
            note_at = now + duration + 30
            note += 1
    else:
        flag_servo.disable()

    screen.pen = INK
    screen.clear()
    draw_flag(now, waving)

    screen.font = TITLE_FONT
    screen.pen = PAPER
    screen.text("Hooray!" if waving else "", rect(110, 150, 200, 40), 30)
    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text(f"Waved {waves} time{'' if waves == 1 else 's'}", 210, 196, 13)
    screen.text("A or switch  Wave    Servo 1  Switch GP3", 12, 220, 13)

    explorer.update()

"""Mood Lamp
Turn the dial to pick a colour.

You will need:
- RGB LED
- Potentiometer
- 7 wires

Icon: table_lamp
"""
import math

import explorer
from explorer import ADC0, GP2, GP3, GP4, SELECT, UP, Analog, Output, labels, screen, wiring
from picovector import color, font, image, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)

SEGMENTS = 36
CENTRE_X = 160
CENTRE_Y = 134
RING_INNER = 66
RING_OUTER = 88
CYCLE_MS = 30000
BREATHE_MS = 6000
SMOOTHING = 0.08

POT_STEPS = (
    (
        "Pot pins-up in columns 4, 5, 6 above the groove, shaft over the groove",
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
RGB_LED_COLUMN = 13
WIRING = (
    (
        "RGB LED in columns 13 to 16, bottom half. Longest leg (ground) second.",
        (wiring.rgb_led(RGB_LED_COLUMN),),
    ),
    (
        "Wires from R to GP4, G to GP3, B to GP2 and the longest leg to GND",
        tuple(
            wiring.wire(wiring.hole(RGB_LED_COLUMN + offset, 4), end, rgb, (0, 20 + offset * 4), (-20 - offset * 4, 0))
            for offset, end, rgb in (
                (0, wiring.gpio(4), (235, 60, 50)),
                (1, wiring.ground(4), wiring.BLACK),
                (2, wiring.gpio(3), (60, 200, 90)),
                (3, wiring.gpio(2), (70, 120, 255)),
            )
        ),
    ),
) + POT_STEPS

wiring.show(WIRING, BODY_FONT, BODY_FONT)

leds = (Output(GP4), Output(GP3), Output(GP2))
dial = Analog(ADC0)
cycle = True
breathe = False
hue = dial.read()
last = explorer.ticks()
ring = []
for segment in range(SEGMENTS):
    start = segment * 360 / SEGMENTS
    ring.append((shape.arc(CENTRE_X, CENTRE_Y, RING_INNER, RING_OUTER, start, start + 360 / SEGMENTS + 1), color.hsv(int(segment * 255 / SEGMENTS), 255, 255)))

while True:
    now = explorer.ticks()
    elapsed = now - last
    last = now
    if SELECT.pressed:
        cycle = not cycle
    if UP.pressed:
        breathe = not breathe

    if cycle:
        hue = (hue + elapsed / CYCLE_MS) % 1.0
    else:
        hue += (dial.read() - hue) * SMOOTHING
    level = 0.55 + 0.45 * math.sin(now * 2 * math.pi / BREATHE_MS) if breathe else 1.0

    lamp = color.hsv(int(hue * 255), 255, int(255 * level)).to_rgb()
    for led, value in zip(leds, (lamp.r, lamp.g, lamp.b)):
        led.brightness((value / 255) ** 2)

    screen.pen = INK
    screen.clear()
    for segment, pen in ring:
        screen.pen = pen
        screen.shape(segment)

    angle = math.radians(hue * 360 - 90)
    marker_x = CENTRE_X + math.cos(angle) * (RING_INNER + RING_OUTER) / 2
    marker_y = CENTRE_Y + math.sin(angle) * (RING_INNER + RING_OUTER) / 2
    screen.pen = INK
    screen.shape(shape.circle(marker_x, marker_y, 14))
    screen.pen = lamp
    screen.shape(shape.circle(marker_x, marker_y, 10))
    screen.shape(shape.circle(CENTRE_X, CENTRE_Y, 52))

    labels.draw(screen, TITLE_FONT, {"A": "Cycle on" if cycle else "Cycle off", "X": "Breathe on" if breathe else "Breathe off"})

    explorer.update()

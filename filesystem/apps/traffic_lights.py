"""Traffic Lights
Run a UK traffic light sequence.

You will need:
- Red, yellow, green LEDs
- 1 wire

Icon: traffic
"""
import explorer
from explorer import DOWN, GP0, GP2, GP4, SELECT, Output, labels, screen
from explorer import wiring
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)
HOUSING = color.rgb(12, 12, 12)

WIRING = (
    (
        "Long leg + into GP0, GP2, GP4. Short leg - into the end column.",
        (wiring.led(0, (235, 60, 50)), wiring.led(2, (255, 190, 40)), wiring.led(4, (60, 200, 90))),
    ),
    ("Black wire from the end column to GND", (wiring.wire(wiring.hole(16, 3), wiring.ground(4), wiring.BLACK),)),
)

LAMPS = (
    ((235, 60, 50), 64),
    ((255, 190, 40), 120),
    ((60, 200, 90), 176),
)

STAGES = (
    ("Stop", (1, 0, 0), 4000),
    ("Get ready", (1, 1, 0), 1500),
    ("Go", (0, 0, 1), 4000),
    ("Stop if safe", (0, 1, 0), 2000),
)

wiring.show(WIRING, TITLE_FONT, BODY_FONT)

leds = (Output(GP0), Output(GP2), Output(GP4))
stage = 0
stage_started = explorer.ticks()

while True:
    if DOWN.pressed:
        wiring.show(WIRING, TITLE_FONT, BODY_FONT)
        stage_started = explorer.ticks()

    now = explorer.ticks()
    if SELECT.pressed or now - stage_started >= STAGES[stage][2]:
        stage = (stage + 1) % len(STAGES)
        stage_started = now

    name, lit, duration = STAGES[stage]
    for led, on in zip(leds, lit):
        led.value(on)

    screen.pen = INK
    screen.clear()

    screen.pen = HOUSING
    screen.shape(shape.rounded_rectangle(72, 24, 92, 192, 24))
    for ((r, g, b), y), on in zip(LAMPS, lit):
        if on:
            screen.pen = color.rgb(r, g, b, 60)
            screen.shape(shape.circle(118, y, 34))
            screen.pen = color.rgb(r, g, b)
        else:
            screen.pen = color.rgb(r // 6, g // 6, b // 6)
        screen.shape(shape.circle(118, y, 24))

    screen.font = TITLE_FONT
    screen.pen = PAPER
    screen.text(name, rect(180, 60, 136, 44), 24, align=(image.LEFT, image.MIDDLE))

    progress = min(1.0, (now - stage_started) / duration)
    screen.pen = FAINT
    screen.shape(shape.rounded_rectangle(180, 151, 120, 8, 4))
    screen.pen = PAPER
    screen.shape(shape.rounded_rectangle(180, 151, 8 + 112 * progress, 8, 4))

    labels.draw(screen, TITLE_FONT, {"A": "Next", "Y": "Wiring"})

    explorer.update()

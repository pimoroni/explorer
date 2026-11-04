"""Blink
Dim and flash five LEDs.

You will need:
- Red, yellow, green, blue, white LEDs

Icon: lightbulb
"""
import explorer
from explorer import GP0, GP1, GP2, GP3, GP4, Output, button_a, button_b, button_c, button_x, button_y, button_z, screen, wiring
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)

LED_RGB = ((235, 60, 50), (255, 190, 40), (60, 200, 90), (70, 120, 255), (239, 235, 227))
LED_COLUMNS = (0, 4, 8, 12, 16)
LED_PINS = (4, 3, 2, 1, 0)
WIRING = (
    (
        "LEDs across the groove at columns 0, 4, 8, 12, 16. Long leg + above, short leg - below.",
        tuple(wiring.led_across(column, rgb) for column, rgb in zip(LED_COLUMNS, LED_RGB)),
    ),
    (
        "Wires from each long leg to GP4, GP3, GP2, GP1, GP0",
        tuple(
            wiring.wire(wiring.hole(column, 1, True), wiring.gpio(pin), rgb, (0, -14 - pin * 5), (-30 - pin * 4, -20))
            for column, pin, rgb in zip(LED_COLUMNS, LED_PINS, LED_RGB)
        ),
    ),
    (
        "Black and grey wires join the short legs, then black to GND",
        tuple(
            wiring.wire(wiring.hole(column, 3), wiring.hole(column + 4, 3), rgb, (8, 14), (-8, 14))
            for column, rgb in zip(LED_COLUMNS, (wiring.BLACK, wiring.GREY, wiring.GREY, wiring.GREY))
        )
        + (wiring.wire(wiring.hole(16, 2), wiring.ground(4), wiring.BLACK, (20, 30), (0, 30)),),
    ),
)

STEPS = 10
GAMMA = 2.5
BLINK_PERIOD_MS = 1000
PWM_HZ = 1000
SLIDER_SPACING = 64
TRACK_TOP = 50
TRACK_HEIGHT = 110
TRACK_WIDTH = 18

wiring.show(WIRING, TITLE_FONT, BODY_FONT)

leds = (Output(GP4), Output(GP3), Output(GP2), Output(GP1), Output(GP0))
levels = [10, 7, 5, 3, 1]
lit = [True] * 5
blinking = [False, False, False, False, True]
selected = 0

while True:
    now = explorer.ticks()
    if button_c.pressed:
        selected = (selected - 1) % 5
    if button_z.pressed:
        selected = (selected + 1) % 5
    if button_x.pressed:
        levels[selected] = min(STEPS, levels[selected] + 1)
    if button_y.pressed:
        levels[selected] = max(0, levels[selected] - 1)
    if button_a.pressed:
        lit[selected] = not lit[selected]
    if button_b.pressed:
        blinking[selected] = not blinking[selected]

    screen.pen = INK
    screen.clear()

    for index, led in enumerate(leds):
        level = levels[index] / STEPS
        if not lit[index]:
            output = 0.0
        elif blinking[index]:
            output = 1.0 if now % BLINK_PERIOD_MS < level * BLINK_PERIOD_MS else 0.0
        else:
            output = level ** GAMMA
        if output in (0.0, 1.0):
            led.value(output)
        else:
            led.brightness(output)

        r, g, b = LED_RGB[index]
        x = SLIDER_SPACING / 2 + index * SLIDER_SPACING
        glow = output ** (1 / GAMMA)
        screen.pen = color.rgb(int(r * glow), int(g * glow), int(b * glow)) if glow > 0 else FAINT
        screen.shape(shape.circle(x, 24, 14))

        if index == selected:
            screen.pen = FAINT
            screen.shape(shape.rounded_rectangle(x - 29, TRACK_TOP - 8, 58, 160, 8))

        screen.pen = color.rgb(14, 14, 14)
        screen.shape(shape.rounded_rectangle(x - TRACK_WIDTH / 2, TRACK_TOP, TRACK_WIDTH, TRACK_HEIGHT, TRACK_WIDTH / 2))
        fill = TRACK_HEIGHT * level
        if fill > 0:
            screen.pen = color.rgb(r, g, b) if lit[index] else DIM
            screen.shape(shape.rounded_rectangle(x - TRACK_WIDTH / 2, TRACK_TOP + TRACK_HEIGHT - fill, TRACK_WIDTH, fill, min(TRACK_WIDTH, fill) / 2))

        screen.font = TITLE_FONT
        screen.pen = PAPER if lit[index] else DIM
        label = f"{levels[index] * 10}%" if lit[index] else "Off"
        screen.text(label, rect(x - 30, TRACK_TOP + TRACK_HEIGHT + 4, 60, 22), 16, align=(image.CENTER, image.MIDDLE))
        screen.font = BODY_FONT
        screen.pen = DIM
        mode = "1 Hz" if blinking[index] else "Dim"
        screen.text(f"GP{LED_PINS[index]} {mode}", rect(x - 30, TRACK_TOP + TRACK_HEIGHT + 24, 60, 18), 12, align=(image.CENTER, image.MIDDLE))

    screen.font = BODY_FONT
    screen.pen = PAPER
    screen.text("C Z  Choose    X Y  Up / down", 10, 202, 14)
    screen.text("A  On / off    B  Dim / blink", 10, 220, 14)

    explorer.update()

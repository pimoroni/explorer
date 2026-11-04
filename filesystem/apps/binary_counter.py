"""Binary Counter
Count to 31 on five LEDs.

You will need:
- Red, yellow, green, blue, white LEDs

Icon: calculate
"""
import explorer
from explorer import BACK, DOWN, GP0, GP1, GP2, GP3, GP4, SELECT, UP, Output, labels, screen, wiring
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)
BULB_COLOURS = (
    color.rgb(235, 60, 50),
    color.rgb(255, 190, 40),
    color.rgb(60, 200, 90),
    color.rgb(70, 120, 255),
    color.rgb(239, 235, 227),
)

VALUES = (16, 8, 4, 2, 1)
BULB_Y = 158
DIGIT_SIZE = 20
CAP_CENTRE = 0.64
AUTO_MS = 800

LED_RGB = ((235, 60, 50), (255, 190, 40), (60, 200, 90), (70, 120, 255), (239, 235, 227))
LED_COLUMNS = (0, 4, 8, 12, 16)
LED_PINS = (4, 3, 2, 1, 0)
WIRING = (
    (
        "LEDs across the groove at columns 0, 4, 8, 12, 16. Long leg + above.",
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

wiring.show(WIRING, TITLE_FONT, BODY_FONT)

leds = (Output(GP4), Output(GP3), Output(GP2), Output(GP1), Output(GP0))
count = 0
auto = False
last_step = 0

while True:
    now = explorer.ticks()
    if BACK.pressed:
        count = 0
    if DOWN.pressed:
        wiring.show(WIRING, TITLE_FONT, BODY_FONT)
    if UP.pressed:
        auto = not auto
    if SELECT.pressed or (auto and now - last_step >= AUTO_MS):
        count = (count + 1) % 32
        last_step = now
        explorer.beep(440 + count * 20, 30)

    bits = [bool(count & value) for value in VALUES]
    for led, on in zip(leds, bits):
        led.value(on)

    screen.pen = INK
    screen.clear()

    sum_text = " + ".join(str(value) for value, on in zip(VALUES, bits) if on) or "0"
    screen.font = TITLE_FONT
    screen.pen = PAPER
    screen.text(f"{sum_text} = {count}", rect(0, 64, 320, 36), 26, align=(image.CENTER, image.MIDDLE))

    for index, (value, on, pen) in enumerate(zip(VALUES, bits, BULB_COLOURS)):
        x = 64 + index * 48
        screen.pen = pen if on else FAINT
        screen.shape(shape.circle(x, BULB_Y, 18))
        screen.font = TITLE_FONT
        screen.pen = INK if on else DIM
        digit = "1" if on else "0"
        digit_width = screen.measure_text(digit, font_size=DIGIT_SIZE)[0]
        screen.text(digit, x - digit_width / 2, BULB_Y - DIGIT_SIZE * CAP_CENTRE, DIGIT_SIZE)
        screen.font = BODY_FONT
        screen.pen = DIM
        screen.text(str(value), rect(x - 20, 182, 40, 22), 18, align=(image.CENTER, image.MIDDLE))

    labels.draw(screen, TITLE_FONT, {"A": "+1", "B": labels.Icon("change_circle"), "X": labels.Icon("pause_circle" if auto else "play_circle"), "Y": "Wiring"}, "A")

    explorer.update()

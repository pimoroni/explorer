"""Colour Mixer
Mix any colour with red, green and blue light.

You will need:
- Red, green, blue LEDs or an RGB LED

Icon: palette
"""
import explorer
from explorer import DOWN, GP2, GP3, GP4, SELECT, UP, Output, button_c, button_x, button_z, labels, screen, wiring
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)

CHANNELS = (("R", (235, 60, 50)), ("G", (60, 200, 90)), ("B", (70, 120, 255)))
SLIDER_TOP = 12
SLIDER_HEIGHT = 158
SPEED = 0.5
MAX_DUTY = 0.5

LED_RGB = tuple(rgb for _, rgb in CHANNELS)
LED_COLUMNS = (0, 4, 8)
LED_PINS = (4, 3, 2)
LED_WIRING = (
    (
        "Red, green, blue LEDs across the groove at columns 0, 4, 8. Long leg + above.",
        tuple(wiring.led_across(column, rgb) for column, rgb in zip(LED_COLUMNS, LED_RGB)),
    ),
    (
        "Wires from each long leg to GP4, GP3, GP2",
        tuple(
            wiring.wire(wiring.hole(column, 1, True), wiring.gpio(pin), rgb, (0, -14 - pin * 5), (-30 - pin * 4, -20))
            for column, pin, rgb in zip(LED_COLUMNS, LED_PINS, LED_RGB)
        ),
    ),
    (
        "Black and grey wires join the short legs, then black to GND",
        tuple(
            wiring.wire(wiring.hole(column, 3), wiring.hole(column + 4, 3), rgb, (8, 14), (-8, 14))
            for column, rgb in zip((0, 4, 8, 12), (wiring.BLACK, wiring.GREY, wiring.GREY, wiring.GREY))
        )
        + (wiring.wire(wiring.hole(16, 2), wiring.ground(4), wiring.BLACK, (20, 30), (0, 30)),),
    ),
)

RGB_LED_COLUMN = 13
RGB_LED_WIRING = (
    (
        "RGB LED in columns 13 to 16, bottom half. Longest leg (ground) second.",
        (wiring.rgb_led(RGB_LED_COLUMN),),
    ),
    (
        "Wires from R to GP4, G to GP3, B to GP2 and the longest leg to GND",
        tuple(
            wiring.wire(wiring.hole(RGB_LED_COLUMN + offset, 4), end, rgb, (0, 20 + offset * 4), (-20 - offset * 4, 0))
            for offset, end, rgb in (
                (0, wiring.gpio(4), LED_RGB[0]),
                (1, wiring.ground(4), wiring.BLACK),
                (2, wiring.gpio(3), LED_RGB[1]),
                (3, wiring.gpio(2), LED_RGB[2]),
            )
        ),
    ),
)


def choose_wiring():
    while True:
        if SELECT.pressed:
            return LED_WIRING
        if button_x.pressed:
            return RGB_LED_WIRING
        screen.pen = INK
        screen.clear()
        screen.font = TITLE_FONT
        screen.pen = PAPER
        screen.text("Which LEDs?", rect(0, 0, 320, 32), 22, align=(image.CENTER, image.MIDDLE))
        for index, (title, dots) in enumerate((("Red, green, blue LEDs", 3), ("RGB LED", 1))):
            x = 12 + index * 152
            screen.pen = FAINT
            screen.shape(shape.rounded_rectangle(x, 66, 144, 166, 12))
            if dots == 3:
                for dot, (r, g, b) in enumerate(LED_RGB):
                    screen.pen = color.rgb(r, g, b)
                    screen.shape(shape.circle(x + 40 + dot * 32, 120, 13))
            else:
                screen.pen = color.rgb(236, 236, 240)
                screen.shape(shape.circle(x + 72, 120, 22))
                for dot, (r, g, b) in enumerate(LED_RGB):
                    screen.pen = color.rgb(r, g, b, 140)
                    screen.shape(shape.circle(x + 62 + dot * 10, 124, 6))
            screen.font = BODY_FONT
            screen.pen = PAPER
            screen.text(title, rect(x + 8, 160, 128, 64), 17, align=(image.CENTER, image.MIDDLE))
        labels.draw(screen, TITLE_FONT, {"A": "Three LEDs", "X": "RGB LED"})
        explorer.update()


wiring.show(choose_wiring(), TITLE_FONT, BODY_FONT)

leds = (Output(GP4), Output(GP3), Output(GP2))
levels = [1.0, 0.5, 0.0]
selected = 0
last = explorer.ticks()

while True:
    now = explorer.ticks()
    step = SPEED * (now - last) / 1000
    last = now
    if button_z.pressed:
        selected = (selected + 1) % 3
    if button_c.pressed:
        selected = (selected - 1) % 3
    if UP.held:
        levels[selected] = min(1.0, levels[selected] + step)
    if DOWN.held:
        levels[selected] = max(0.0, levels[selected] - step)

    for led, level in zip(leds, levels):
        led.brightness(level * level * MAX_DUTY)

    screen.pen = INK
    screen.clear()

    for index, ((name, (r, g, b)), level) in enumerate(zip(CHANNELS, levels)):
        x = 22 + index * 46
        screen.pen = FAINT
        screen.shape(shape.rounded_rectangle(x, SLIDER_TOP, 28, SLIDER_HEIGHT, 14))
        fill = 28 + (SLIDER_HEIGHT - 28) * level
        screen.pen = color.rgb(r, g, b)
        screen.shape(shape.rounded_rectangle(x, SLIDER_TOP + SLIDER_HEIGHT - fill, 28, fill, 14))
        screen.font = TITLE_FONT
        screen.pen = PAPER if index == selected else DIM
        screen.text(name, rect(x - 10, 206, 48, 20), 18, align=(image.CENTER, image.MIDDLE))
        if index == selected:
            screen.shape(shape.rounded_rectangle(x + 4, 230, 20, 4, 2))

    red, green, blue = (int(level * 255) for level in levels)
    screen.pen = color.rgb(red, green, blue)
    screen.shape(shape.rounded_rectangle(164, 12, 88, 88, 16))

    screen.font = TITLE_FONT
    screen.pen = PAPER
    screen.text(f"#{red:02X}{green:02X}{blue:02X}", rect(150, 106, 116, 26), 20, align=(image.CENTER, image.MIDDLE))
    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text(f"{red} {green} {blue}", rect(150, 136, 116, 22), 16, align=(image.CENTER, image.MIDDLE))

    labels.draw(screen, TITLE_FONT, {"C": "Left", "X": "More", "Y": "Less", "Z": "Right"})

    explorer.update()

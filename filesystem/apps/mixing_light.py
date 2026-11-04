"""Mixing Light
Red, green and blue make every colour.

You will need:
- Red, green, blue LEDs
- RGB LED
- 8 wires

Icon: join
"""
import explorer
from explorer import GP0, GP1, GP2, GP3, GP4, GP5, SELECT, Output, button_x, button_y, button_z, labels, screen
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)

PRIMARIES = (
    ("Red", (255, 0, 0), button_x, "X", 45),
    ("Green", (0, 255, 0), button_y, "Y", 119),
    ("Blue", (0, 0, 255), button_z, "Z", 191),
)

NAMES = {
    (0, 0, 0): "Off",
    (1, 0, 0): "Red",
    (0, 1, 0): "Green",
    (0, 0, 1): "Blue",
    (1, 1, 0): "Yellow",
    (1, 0, 1): "Magenta",
    (0, 1, 1): "Cyan",
    (1, 1, 1): "White",
}

DEMO = ((1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (0, 1, 1), (1, 0, 1), (1, 1, 1))

single_leds = (Output(GP0), Output(GP1), Output(GP2))
rgb_led = (Output(GP4), Output(GP3), Output(GP5))
mix = [1, 1, 0]
demo = False
demo_step = 0
demo_started = 0

while True:
    now = explorer.ticks()
    for channel, (_, _, button, _, _) in enumerate(PRIMARIES):
        if button.pressed:
            mix[channel] = 1 - mix[channel]
            demo = False
    if SELECT.pressed:
        demo = not demo
        demo_started = now - 2000
    if demo and now - demo_started >= 1500:
        demo_step = (demo_step + 1) % len(DEMO)
        demo_started = now
        mix = list(DEMO[demo_step])

    for channel in range(3):
        single_leds[channel].value(mix[channel])
        rgb_led[channel].value(mix[channel])

    screen.pen = INK
    screen.clear()

    r, g, b = (255 * on for on in mix)
    if any(mix):
        screen.pen = color.rgb(r, g, b, 50)
        screen.shape(shape.circle(110, 112, 76))
        screen.pen = color.rgb(r, g, b)
    else:
        screen.pen = FAINT
    screen.shape(shape.circle(110, 112, 62))

    screen.font = TITLE_FONT
    screen.pen = PAPER
    screen.text(NAMES[tuple(mix)], rect(10, 190, 200, 30), 24, align=(image.CENTER, image.MIDDLE))

    actions = {"A": "Stop" if demo else "Demo"}
    for (name, (pr, pg, pb), _, letter, y), on in zip(PRIMARIES, mix):
        screen.pen = color.rgb(pr, pg, pb) if on else FAINT
        screen.shape(shape.circle(234, y, 18))
        actions[letter] = name

    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text("+", rect(222, 70, 24, 24), 20, align=(image.CENTER, image.MIDDLE))
    screen.text("+", rect(222, 143, 24, 24), 20, align=(image.CENTER, image.MIDDLE))

    labels.draw(screen, TITLE_FONT, actions, None if demo else "A")

    explorer.update()

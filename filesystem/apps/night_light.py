"""Night Light
Turns an LED on when it gets dark.

You will need:
- Multi-Sensor Stick
- White LED
- 2 wires

Icon: nightlight
"""
import math

import explorer
from breakout_ltr559 import BreakoutLTR559
from explorer import DOWN, GP0, UP, Output, labels, screen
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

ltr = explorer.sensor(BreakoutLTR559, TITLE_FONT)

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)
GLOW = color.rgb(255, 204, 51)

BAR = (40, 170, 240, 12)
LOG_MIN = -1
LOG_MAX = 4
FADE_SPEED = 0.05


led = Output(GP0)
threshold = 20.0
lux = 0.0
level = 0.0


def bar_x(value):
    x, _, width, _ = BAR
    position = (math.log10(max(value, 0.1)) - LOG_MIN) / (LOG_MAX - LOG_MIN)
    return x + width * max(0.0, min(1.0, position))


while True:
    if UP.pressed:
        threshold = min(1000, threshold * 1.5)
    if DOWN.pressed:
        threshold = max(1, threshold / 1.5)

    reading = ltr.get_reading()
    if reading is not None:
        lux = reading[BreakoutLTR559.LUX]
    dark = lux < threshold
    level += ((1.0 if dark else 0.0) - level) * FADE_SPEED
    led.brightness(level * level)

    screen.pen = INK
    screen.clear()

    if level > 0.05:
        screen.pen = color.rgb(255, 204, 51, int(80 * level))
        screen.shape(shape.circle(62, 66, 40 + 16 * level))
    screen.pen = GLOW if level > 0.05 else FAINT
    screen.shape(shape.circle(62, 66, 40))
    screen.pen = INK
    screen.shape(shape.circle(80, 52, 34))

    reading_text = f"{lux:.0f}"
    screen.font = TITLE_FONT
    screen.pen = PAPER
    screen.text(reading_text, 122, 22, 32)
    unit_x = 128 + screen.measure_text(reading_text, font_size=32)[0]
    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text("lux", unit_x, 36, 18)
    screen.text("Dark, light on" if dark else "Bright, light off", 122, 70, 18)

    x, y, width, height = BAR
    screen.pen = FAINT
    screen.shape(shape.rounded_rectangle(x, y, width, height, height / 2))
    screen.pen = GLOW
    screen.shape(shape.rounded_rectangle(x, y, max(height, bar_x(lux) - x), height, height / 2))
    marker = bar_x(threshold)
    screen.pen = PAPER
    screen.shape(shape.rectangle(marker - 1, y - 8, 3, height + 16))
    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text("dark", rect(x, y + 22, width, 16), 14, align=(image.LEFT, image.TOP))
    screen.text("sunny", rect(x, y + 22, width, 16), 14, align=(image.RIGHT, image.TOP))
    screen.pen = PAPER
    screen.text(f"Switch on below {threshold:.0f} lux", rect(0, y - 32, 320, 18), 17, align=(image.CENTER, image.TOP))

    screen.pen = DIM
    screen.text("LED GP0", rect(0, 218, 320, 16), 14, align=(image.CENTER, image.TOP))

    labels.draw(screen, TITLE_FONT, {"X": labels.UP, "Y": labels.DOWN})

    explorer.update()

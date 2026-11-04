"""Thermometer
Too cold, too hot, or just right?

You will need:
- Multi-Sensor Stick
- Blue, green, red LEDs
- 4 wires

Icon: device_thermostat
"""
import explorer
from breakout_bme280 import BreakoutBME280
from explorer import GP0, GP1, GP2, SELECT, Output, labels, screen
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

bme = explorer.sensor(BreakoutBME280, TITLE_FONT)

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)
COLD_COLOUR = color.rgb(70, 120, 255)
COMFY_COLOUR = color.rgb(60, 200, 90)
HOT_COLOUR = color.rgb(235, 60, 50)

COLD = 18
HOT = 24
SCALE_MIN = 0
SCALE_MAX = 40
TUBE_TOP = 24
TUBE_BOTTOM = 170
READ_MS = 1000

cold_led, comfy_led, hot_led = Output(GP0), Output(GP1), Output(GP2)
fahrenheit = False
temperature = bme.read()[0]
next_read = explorer.ticks() + READ_MS
gauge = 0.0

while True:
    now = explorer.ticks()
    if SELECT.pressed:
        fahrenheit = not fahrenheit
    if now >= next_read:
        temperature = bme.read()[0]
        next_read = now + READ_MS

    if temperature < COLD:
        mood, pen = "Chilly", COLD_COLOUR
    elif temperature > HOT:
        mood, pen = "Toasty", HOT_COLOUR
    else:
        mood, pen = "Comfy", COMFY_COLOUR
    cold_led.value(temperature < COLD)
    comfy_led.value(COLD <= temperature <= HOT)
    hot_led.value(temperature > HOT)

    screen.pen = INK
    screen.clear()

    screen.pen = FAINT
    screen.shape(shape.rounded_rectangle(252, TUBE_TOP - 6, 24, TUBE_BOTTOM - TUBE_TOP + 20, 12))
    screen.shape(shape.circle(264, 190, 26))
    level = max(0.0, min(1.0, (temperature - SCALE_MIN) / (SCALE_MAX - SCALE_MIN)))
    gauge += (level - gauge) * 0.15
    top = TUBE_BOTTOM - (TUBE_BOTTOM - TUBE_TOP) * gauge
    screen.pen = pen
    screen.shape(shape.rounded_rectangle(258, top, 12, 196 - top, 6))
    screen.shape(shape.circle(264, 190, 20))

    screen.font = BODY_FONT
    for mark in range(SCALE_MIN, SCALE_MAX + 1, 10):
        y = TUBE_BOTTOM - (TUBE_BOTTOM - TUBE_TOP) * (mark - SCALE_MIN) / (SCALE_MAX - SCALE_MIN)
        screen.pen = FAINT
        screen.shape(shape.line(238, y, 246, y, 2))
        screen.pen = DIM
        screen.text(str(mark), rect(200, y - 8, 34, 16), 14, align=(image.RIGHT, image.MIDDLE))

    shown = temperature * 9 / 5 + 32 if fahrenheit else temperature
    screen.font = TITLE_FONT
    screen.pen = PAPER
    screen.text(f"{shown:.1f}°{'F' if fahrenheit else 'C'}", rect(12, 60, 190, 48), 44, align=(image.CENTER, image.MIDDLE))
    screen.pen = pen
    screen.text(mood, rect(12, 108, 190, 36), 28, align=(image.CENTER, image.MIDDLE))

    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text(f"Comfy is {COLD}-{HOT}°C", rect(12, 146, 190, 20), 16, align=(image.CENTER, image.MIDDLE))
    screen.text("Blue GP0  Green GP1  Red GP2", rect(12, 212, 230, 20), 14, align=(image.LEFT, image.MIDDLE))

    labels.draw(screen, TITLE_FONT, {"A": "Celsius" if fahrenheit else "Fahrenheit"})

    explorer.update()

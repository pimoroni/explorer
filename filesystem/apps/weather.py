"""Weather
Forecast the weather like a barometer.

You will need:
- Multi-Sensor Stick

Icon: partly_cloudy_day
"""
from array import array

import explorer
from breakout_bme280 import BreakoutBME280
from explorer import screen
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

bme = explorer.sensor(BreakoutBME280, TITLE_FONT)

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)
ACCENT = color.rgb(92, 150, 255)

FORECASTS = (
    (970, "Stormy"),
    (990, "Rain"),
    (1010, "Change"),
    (1030, "Fair"),
    (9999, "Very dry"),
)
SAMPLE_MS = 60000
HISTORY = 120
GRAPH = (16, 158, 288, 52)
READ_MS = 1000


history = []
next_sample = explorer.ticks()


def card(x, label, value):
    screen.pen = FAINT
    screen.shape(shape.rounded_rectangle(x, 80, 92, 64, 10))
    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text(label, x + 9, 86, 14)
    screen.font = TITLE_FONT
    screen.pen = PAPER
    screen.text(value, x + 9, 108, 20)


temperature, pressure, humidity = bme.read()
next_read = explorer.ticks() + READ_MS

while True:
    now = explorer.ticks()
    if now >= next_read:
        temperature, pressure, humidity = bme.read()
        next_read = now + READ_MS
    hpa = pressure / 100
    if now >= next_sample:
        history.append(hpa)
        history = history[-HISTORY:]
        next_sample = now + SAMPLE_MS

    forecast = next(name for limit, name in FORECASTS if hpa < limit)
    trend = ""
    if len(history) > 60:
        change = history[-1] - history[-61]
        trend = "rising" if change > 1 else "falling" if change < -1 else "steady"

    screen.pen = INK
    screen.clear()

    screen.font = TITLE_FONT
    screen.pen = PAPER
    screen.text(forecast, 16, 10, 40)
    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text(f"Pressure {trend}" if trend else "Watching the pressure...", 16, 54, 17)

    card(16, "Temperature", f"{temperature:.1f}°C")
    card(114, "Humidity", f"{humidity:.0f}%")
    card(212, "Pressure", f"{hpa:.0f}hPa")

    x, y, width, height = GRAPH
    screen.pen = FAINT
    screen.shape(shape.line(x, y + height, x + width, y + height, 1))
    if len(history) > 1:
        low = min(history) - 1
        high = max(history) + 1
        points = array("f")
        for index, value in enumerate(history):
            points.append(x + width * index / (HISTORY - 1))
            points.append(y + height - height * (value - low) / (high - low))
        screen.pen = ACCENT
        screen.shape(shape.custom(points).stroke(2, shape.PATH_OPEN | shape.JOIN_ROUND | shape.CAP_ROUND))
    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text("Last 2 hours", rect(x, y + height + 6, width, 16), 14, align=(image.RIGHT, image.TOP))

    explorer.update()

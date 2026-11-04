"""Theremin
Hover a finger just above the sensor to play.

You will need:
- Multi-Sensor Stick

Icon: music_note
"""
import math
from array import array

import explorer
from breakout_ltr559 import BreakoutLTR559
from explorer import SELECT, button_c, screen
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")


def proximity_sensor(bus):
    sensor = BreakoutLTR559(bus)
    sensor.proximity_led(100, 100, 30, 8)
    sensor.proximity_measurement_rate(50)
    return sensor


ltr = explorer.sensor(proximity_sensor, TITLE_FONT, on_disconnect=explorer.stop_tone)

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)
WAVE = color.rgb(255, 143, 177)

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
PENTATONIC = (0, 2, 4, 7, 9)
LOWEST = 48
RANGE = 24
NEAR = 360
FAR = 10
SMOOTHING = 0.35


sound = True
snap = True
proximity = 0
note = None


def frequency(midi):
    return 440 * 2 ** ((midi - 69) / 12)


while True:
    if SELECT.pressed:
        sound = not sound
    if button_c.pressed:
        snap = not snap

    reading = ltr.get_reading()
    if reading is not None:
        proximity += (reading[BreakoutLTR559.PROXIMITY] - proximity) * SMOOTHING
    closeness = math.sqrt(max(0.0, min(1.0, (proximity - FAR) / (NEAR - FAR))))

    if closeness > 0:
        midi = LOWEST + closeness * RANGE
        if snap:
            octave, step = divmod(round(midi), 12)
            step = min(PENTATONIC, key=lambda degree: abs(degree - step))
            midi = octave * 12 + step
        note = midi
        if sound:
            explorer.play_tone(frequency(midi))
        else:
            explorer.stop_tone()
    else:
        note = None
        explorer.stop_tone()

    screen.pen = INK
    screen.clear()

    if note is not None:
        cycles = 1 + closeness * 6
        points = array("f")
        for x in range(0, 321, 4):
            points.append(x)
            points.append(122 + math.sin(x / 320 * cycles * 2 * math.pi + explorer.ticks() / 100) * 30 * (0.4 + closeness))
        screen.pen = WAVE
        screen.shape(shape.custom(points).stroke(4, shape.PATH_OPEN | shape.JOIN_ROUND | shape.CAP_ROUND))
        name = NOTE_NAMES[round(note) % 12] + str(round(note) // 12 - 1)
        screen.font = TITLE_FONT
        screen.pen = PAPER
        screen.text(name, 16, 12, 36)
        screen.font = BODY_FONT
        screen.pen = DIM
        screen.text(f"{frequency(note):.0f} Hz", 16, 52, 14)
    else:
        screen.font = BODY_FONT
        screen.pen = DIM
        screen.text("Hover a finger within 3cm of the sensor", rect(0, 96, 320, 24), 16, align=(image.CENTER, image.MIDDLE))

    screen.pen = FAINT
    screen.shape(shape.rounded_rectangle(16, 180, 288, 8, 4))
    screen.pen = WAVE
    screen.shape(shape.rounded_rectangle(16, 180, 8 + 280 * closeness, 8, 4))

    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text(f"A  Sound {'on' if sound else 'off'}    C  {'Scale' if snap else 'Slide'}", 12, 214, 14)

    explorer.update()

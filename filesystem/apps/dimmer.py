"""Dimmer
Fade an LED by switching it on and off really fast.

You will need:
- White LED
- Potentiometer
- 4 wires

Icon: brightness_6
"""
import explorer
from explorer import ADC0, GP0, Analog, Output, screen, wiring
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)
ACCENT = color.rgb(255, 204, 51)

WAVE_LEFT = 20
WAVE_WIDTH = 280
WAVE_HIGH = 120
WAVE_LOW = 180
PERIODS = 4
LINE_WIDTH = 3

POT_STEPS = (
    (
        "Potentiometer pins-up in columns 4, 5, 6 just above the groove, shaft over the groove",
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
WIRING = (
    (
        "White LED: long leg + into GP0, short leg - into the end column",
        (wiring.led(0, (239, 235, 227)),),
    ),
    ("Black wire from the end column to GND", (wiring.wire(wiring.hole(16, 3), wiring.ground(4), wiring.BLACK),)),
) + POT_STEPS

wiring.show(WIRING, TITLE_FONT, BODY_FONT)

led = Output(GP0)
dial = Analog(ADC0)
duty = 0.0

while True:
    duty += (dial.read() - duty) * 0.3
    led.brightness(duty)

    screen.pen = INK
    screen.clear()

    screen.font = TITLE_FONT
    screen.pen = PAPER
    screen.text(f"{round(duty * 100)}%", 20, 14, 44)
    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text("of the time the LED is on", rect(150, 26, 160, 40), 14)

    screen.pen = FAINT
    screen.shape(shape.line(WAVE_LEFT, WAVE_LOW, WAVE_LEFT + WAVE_WIDTH, WAVE_LOW, 1))
    screen.pen = ACCENT
    half = LINE_WIDTH / 2
    period = WAVE_WIDTH / PERIODS
    if duty < 0.01 or duty > 0.99:
        level_y = WAVE_LOW if duty < 0.01 else WAVE_HIGH
        screen.shape(shape.rectangle(WAVE_LEFT - half, level_y - half, WAVE_WIDTH + LINE_WIDTH, LINE_WIDTH))
    else:
        for index in range(PERIODS):
            start = WAVE_LEFT + index * period
            high_until = start + period * duty
            screen.shape(shape.rectangle(start - half, WAVE_HIGH - half, LINE_WIDTH, WAVE_LOW - WAVE_HIGH + LINE_WIDTH))
            screen.shape(shape.rectangle(start - half, WAVE_HIGH - half, high_until - start + LINE_WIDTH, LINE_WIDTH))
            screen.shape(shape.rectangle(high_until - half, WAVE_HIGH - half, LINE_WIDTH, WAVE_LOW - WAVE_HIGH + LINE_WIDTH))
            screen.shape(shape.rectangle(high_until - half, WAVE_LOW - half, start + period - high_until + LINE_WIDTH, LINE_WIDTH))

    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text("on", 0, WAVE_HIGH - 8, 12)
    screen.text("off", 0, WAVE_LOW - 8, 12)
    screen.text("LED GP0  Dial ADC0", 12, 214, 14)

    explorer.update()

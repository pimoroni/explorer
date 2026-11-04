"""Crossing
Press the button and wait for the green man.

You will need:
- Red, yellow, green LEDs
- Switch
- 3 wires

Icon: directions_walk
"""
import explorer
from explorer import GP0, GP2, GP4, GP5, SELECT, Input, Output, button_c, screen
from explorer import wiring
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
HOUSING = color.rgb(12, 12, 12)
LAMP_COLOURS = ((235, 60, 50), (255, 190, 40), (60, 200, 90))
MAN_RED = color.rgb(235, 60, 50)
MAN_GREEN = color.rgb(60, 200, 90)
MAN_OFF = color.rgb(40, 38, 36)
WAIT_ON = color.rgb(255, 190, 40)

WIRING = (
    (
        "Long leg + into GP0, GP2, GP4. Short leg - into the end column.",
        (wiring.led(0, (235, 60, 50)), wiring.led(2, (255, 190, 40)), wiring.led(4, (60, 200, 90))),
    ),
    ("Black wire from the end column to GND", (wiring.wire(wiring.hole(16, 3), wiring.ground(4), wiring.BLACK),)),
    ("Button across the middle of the breadboard", (wiring.button(1),)),
    (
        "Wires from above the button to GP5 and GND",
        (
            wiring.wire(wiring.hole(1, 1, True), wiring.gpio(5), wiring.RED, (70, -10), (-70, -20)),
            wiring.wire(wiring.hole(3, 1, True), wiring.ground(5), wiring.BROWN, (70, -10), (-70, -20)),
        ),
    ),
)

GREEN, WAITING, AMBER, WALK, FLASHING = range(5)
DURATIONS = {WAITING: 3000, AMBER: 2000, WALK: 6000, FLASHING: 4000}

wiring.show(WIRING, TITLE_FONT, BODY_FONT)

leds = (Output(GP0), Output(GP2), Output(GP4))
switch = Input(GP5)
state = GREEN
state_started = explorer.ticks()
last_beep = 0


def draw_person(x, y, walking, pen):
    screen.pen = pen
    screen.shape(shape.circle(x, y - 34, 8))
    if walking:
        screen.shape(shape.line(x, y - 24, x - 2, y + 4, 8))
        screen.shape(shape.line(x - 2, y + 2, x - 14, y + 30, 7))
        screen.shape(shape.line(x - 2, y + 2, x + 12, y + 30, 7))
        screen.shape(shape.line(x, y - 20, x - 14, y - 4, 6))
        screen.shape(shape.line(x, y - 20, x + 13, y - 6, 6))
    else:
        screen.shape(shape.line(x, y - 24, x, y + 4, 10))
        screen.shape(shape.line(x - 3, y + 2, x - 4, y + 30, 7))
        screen.shape(shape.line(x + 3, y + 2, x + 4, y + 30, 7))
        screen.shape(shape.line(x - 6, y - 20, x - 9, y + 2, 6))
        screen.shape(shape.line(x + 6, y - 20, x + 9, y + 2, 6))


while True:
    if button_c.pressed:
        wiring.show(WIRING, TITLE_FONT, BODY_FONT)

    now = explorer.ticks()
    elapsed = now - state_started
    if state == GREEN and (switch.pressed or SELECT.pressed):
        state, state_started = WAITING, now
        explorer.beep(660, 60)
    elif state in DURATIONS and elapsed >= DURATIONS[state]:
        state = (state + 1) % 5
        state_started = now

    flash_on = (elapsed // 400) % 2 == 0
    if state in (GREEN, WAITING):
        lit = (0, 0, 1)
    elif state == AMBER:
        lit = (0, 1, 0)
    elif state == WALK:
        lit = (1, 0, 0)
    else:
        lit = (0, flash_on, 0)
    for led, on in zip(leds, lit):
        led.value(on)

    if state == WALK and now - last_beep > 300:
        explorer.beep(880, 120)
        last_beep = now

    screen.pen = INK
    screen.clear()

    screen.pen = HOUSING
    screen.shape(shape.rounded_rectangle(30, 40, 64, 144, 18))
    for index, ((r, g, b), on) in enumerate(zip(LAMP_COLOURS, lit)):
        screen.pen = color.rgb(r, g, b) if on else color.rgb(r // 6, g // 6, b // 6)
        screen.shape(shape.circle(62, 72 + index * 40, 16))

    screen.pen = HOUSING
    screen.shape(shape.rounded_rectangle(130, 24, 170, 176, 18))
    walking = state == WALK or (state == FLASHING and flash_on)
    draw_person(180, 82, False, MAN_OFF if walking else MAN_RED)
    draw_person(250, 82, True, MAN_GREEN if walking else MAN_OFF)

    screen.font = TITLE_FONT
    screen.pen = WAIT_ON if state in (WAITING, AMBER) else MAN_OFF
    screen.text("WAIT", rect(130, 140, 170, 40), 28, align=(image.CENTER, image.MIDDLE))

    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text("A or switch  Push to cross    C  Wiring", 12, 204, 13)
    screen.text("LEDs GP0 GP2 GP4  Switch GP5", 12, 222, 13)

    explorer.update()

"""Desk Fan
Spins faster as the room warms up.

You will need:
- Servo and horn
- Paper fan blades
- Multi-Sensor Stick

Icon: mode_fan
"""
import explorer
from breakout_bme280 import BreakoutBME280
from explorer import DOWN, SELECT, UP, labels, screen, wiring
from picovector import color, font, image, mat3, rect, shape
from servo import CONTINUOUS

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")


INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)
BLADE = color.rgb(92, 150, 255)

SERVO = 1
RAMP = 4.0
MIN_DRIVE = 0.3
SPIN_RATE = 2.0
READ_MS = 1000
FAN_X = 92
FAN_Y = 134

WIRING = (
    ("Servo on header 1. Brown wire to GND, on the right.", (wiring.servo(SERVO),)),
)

wiring.show(WIRING, TITLE_FONT, BODY_FONT)
bme = explorer.sensor(BreakoutBME280, TITLE_FONT, on_disconnect=lambda: fan.disable())

fan = explorer.servo(SERVO, CONTINUOUS)

start_temperature = 22.0
always_on = False
angle = 0.0
last = explorer.ticks()
temperature = bme.read()[0]
next_read = last + READ_MS

while True:
    now = explorer.ticks()
    dt = (now - last) / 1000
    last = now

    if UP.pressed:
        start_temperature += 0.5
    if DOWN.pressed:
        start_temperature -= 0.5
    if SELECT.pressed:
        always_on = not always_on

    if now >= next_read:
        temperature = bme.read()[0]
        next_read = now + READ_MS
    speed = 1.0 if always_on else max(0.0, min(1.0, (temperature - start_temperature) / RAMP))
    if speed > 0:
        fan.value(MIN_DRIVE + (1 - MIN_DRIVE) * speed)
    else:
        fan.disable()
    angle = (angle + speed * SPIN_RATE * 360 * dt) % 360

    screen.pen = INK
    screen.clear()

    screen.pen = FAINT
    screen.shape(shape.circle(FAN_X, FAN_Y, 72))
    screen.pen = BLADE if speed > 0 else DIM
    for blade in range(3):
        petal = shape.ellipse(0, -34, 17, 32)
        petal.transform = mat3().translate(FAN_X, FAN_Y).rotate(angle + blade * 120)
        screen.shape(petal)
    screen.pen = PAPER
    screen.shape(shape.circle(FAN_X, FAN_Y, 10))

    screen.font = TITLE_FONT
    screen.pen = PAPER
    screen.text(f"{temperature:.1f}°C", rect(176, 62, 136, 40), 30)
    screen.pen = BLADE if speed > 0 else DIM
    screen.text(f"{round(speed * 100)}%", rect(176, 136, 136, 40), 30)

    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text("Always on" if always_on else f"Starts at {start_temperature:.1f}°C", rect(176, 182, 136, 20), 16)

    labels.draw(screen, TITLE_FONT, {"A": "Auto" if always_on else "Always on", "X": labels.UP, "Y": labels.DOWN})

    explorer.update()

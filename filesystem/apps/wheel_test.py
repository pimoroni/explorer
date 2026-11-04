"""Wheel Test
Spin each wheel to check your robot.

You will need:
- 2 servos with wheels

Icon: toys
"""
import explorer
from explorer import DOWN, SELECT, UP, button_z, screen, wiring
from picovector import color, font, image, mat3, rect, shape
from servo import CONTINUOUS

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)
ACCENT = color.rgb(52, 199, 138)

LEFT_SERVO = 1
RIGHT_SERVO = 2
RIGHT_REVERSED = True
STEP = 0.25
SPIN_RATE = 0.5

WIRING = (
    (
        "Left wheel servo on header 1, right wheel on 2. Brown wire to GND, on the right.",
        (wiring.servo(LEFT_SERVO), wiring.servo(RIGHT_SERVO)),
    ),
)

wiring.show(WIRING, TITLE_FONT, BODY_FONT)

wheels = (
    ("Left", explorer.servo(LEFT_SERVO, CONTINUOUS), 1, 80),
    ("Right", explorer.servo(RIGHT_SERVO, CONTINUOUS), -1 if RIGHT_REVERSED else 1, 240),
)
CHOICES = ("Left", "Right", "Both")
choice = 2
speeds = [0.0, 0.0]
angles = [0.0, 0.0]
last = explorer.ticks()


def draw_wheel(x, y, angle, active):
    screen.pen = PAPER if active else FAINT
    screen.shape(shape.circle(x, y, 50))
    screen.pen = INK
    screen.shape(shape.circle(x, y, 40))
    screen.pen = PAPER if active else FAINT
    for spoke in range(3):
        bar = shape.rounded_rectangle(-4, -38, 8, 76, 4)
        bar.transform = mat3().translate(x, y).rotate(angle + spoke * 60)
        screen.shape(bar)
    screen.shape(shape.circle(x, y, 10))


while True:
    now = explorer.ticks()
    dt = (now - last) / 1000
    last = now

    if SELECT.pressed:
        choice = (choice + 1) % len(CHOICES)
    selected = (0, 1) if choice == 2 else (choice,)
    for index in selected:
        if UP.pressed:
            speeds[index] = min(1.0, speeds[index] + STEP)
        if DOWN.pressed:
            speeds[index] = max(-1.0, speeds[index] - STEP)
    if button_z.pressed:
        speeds = [0.0, 0.0]

    screen.pen = INK
    screen.clear()

    for index, (name, servo, direction, x) in enumerate(wheels):
        if speeds[index]:
            servo.value(speeds[index] * direction)
        else:
            servo.disable()
        angles[index] += speeds[index] * SPIN_RATE * 360 * dt
        active = index in selected
        draw_wheel(x, 96, angles[index], active)
        screen.font = TITLE_FONT
        screen.pen = PAPER if active else DIM
        screen.text(f"{round(speeds[index] * 100)}%", rect(x - 60, 156, 120, 30), 24, align=(image.CENTER, image.MIDDLE))
        screen.font = BODY_FONT
        screen.pen = DIM
        screen.text(f"{name}  {servo.pulse():.0f}us", rect(x - 60, 184, 120, 18), 13, align=(image.CENTER, image.MIDDLE))

    screen.font = BODY_FONT
    screen.pen = ACCENT
    screen.text(f"A  {CHOICES[choice]}", 12, 10, 14)
    screen.pen = DIM
    screen.text("X Y  Faster / slower    Z  Stop", 12, 218, 14)

    explorer.update()

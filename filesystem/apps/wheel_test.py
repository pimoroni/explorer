"""Wheel Test
Spin each wheel to check your robot.

You will need:
- 2 servos with wheels

Icon: toys
"""
import explorer
from explorer import BACK, DOWN, SELECT, UP, button_c, button_z, labels, screen, wiring
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
        "Left wheel servo on header 1, right on 2. Brown wire to GND, on the right.",
        (wiring.servo(LEFT_SERVO), wiring.servo(RIGHT_SERVO)),
    ),
)

wiring.show(WIRING, TITLE_FONT, BODY_FONT)

wheels = (
    ("Left", explorer.servo(LEFT_SERVO, CONTINUOUS), 1, 114),
    ("Right", explorer.servo(RIGHT_SERVO, CONTINUOUS), -1 if RIGHT_REVERSED else 1, 206),
)
CHOICES = ("Left wheel", "Right wheel", "Both wheels")
LEFT, RIGHT, BOTH = range(3)
choice = BOTH
speeds = [0.0, 0.0]
angles = [0.0, 0.0]
last = explorer.ticks()


def draw_wheel(x, y, angle, active):
    screen.pen = PAPER if active else FAINT
    screen.shape(shape.circle(x, y, 40))
    screen.pen = INK
    screen.shape(shape.circle(x, y, 32))
    screen.pen = PAPER if active else FAINT
    for spoke in range(3):
        bar = shape.rounded_rectangle(-3, -30, 6, 60, 3)
        bar.transform = mat3().translate(x, y).rotate(angle + spoke * 60)
        screen.shape(bar)
    screen.shape(shape.circle(x, y, 8))


while True:
    now = explorer.ticks()
    dt = (now - last) / 1000
    last = now

    if button_c.pressed:
        choice = LEFT
    if button_z.pressed:
        choice = RIGHT
    if SELECT.pressed:
        choice = BOTH
    selected = (0, 1) if choice == BOTH else (choice,)
    for index in selected:
        if UP.pressed:
            speeds[index] = min(1.0, speeds[index] + STEP)
        if DOWN.pressed:
            speeds[index] = max(-1.0, speeds[index] - STEP)
    if BACK.pressed:
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
        draw_wheel(x, 82, angles[index], active)
        screen.font = TITLE_FONT
        screen.pen = PAPER if active else DIM
        screen.text(f"{round(speeds[index] * 100)}%", rect(x - 46, 132, 92, 28), 24, align=(image.CENTER, image.MIDDLE))
        screen.font = BODY_FONT
        screen.pen = DIM
        screen.text(f"{name}  {servo.pulse():.0f}us", rect(x - 46, 158, 92, 18), 14, align=(image.CENTER, image.MIDDLE))

    screen.font = TITLE_FONT
    screen.pen = ACCENT
    screen.text(CHOICES[choice], rect(0, 2, 320, 30), 20, align=(image.CENTER, image.TOP))

    actions = {}
    if choice != BOTH:
        actions["A"] = "Both"
    if speeds[0] or speeds[1]:
        actions["B"] = "Stop"
    if choice != LEFT:
        actions["C"] = "Left"
    if any(speeds[index] < 1.0 for index in selected):
        actions["X"] = "Faster"
    if any(speeds[index] > -1.0 for index in selected):
        actions["Y"] = "Slower"
    if choice != RIGHT:
        actions["Z"] = "Right"
    labels.draw(screen, TITLE_FONT, actions)

    explorer.update()

"""Calibrate
Trim your robot until it drives straight.

You will need:
- 2 servos with wheels
- Battery holder
- Multi-Sensor Stick, for auto trim

Icon: tune
"""
import explorer
from explorer import DOWN, SELECT, UP, button_c, button_z, screen, stick, wiring
from explorer.robot import LEFT_SERVO, RIGHT_SERVO, Heading, Robot, save
from lsm6ds3 import LSM6DS3
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)
ACCENT = color.rgb(52, 199, 138)
ALERT = color.rgb(255, 122, 61)

RUN_MS = 3000
WARMUP_MS = 400
TRIM_STEP = 0.01
TRIM_LIMIT = 0.3
AUTO_GAIN = 0.004
AUTO_LIMIT = 0.05
STRAIGHT_DPS = 0.5

WIRING = (
    (
        "Left wheel servo on header 1, right wheel on 2. Brown wire to GND, on the right.",
        (wiring.servo(LEFT_SERVO), wiring.servo(RIGHT_SERVO)),
    ),
)

wiring.show(WIRING, TITLE_FONT, BODY_FONT)

robot = Robot(explorer)
heading = None
if stick.connected(explorer.i2c()):
    heading = Heading(explorer.sensor(LSM6DS3, TITLE_FONT, on_disconnect=robot.stop))

driving = False
run_started = 0
drift = None
drift_total = 0.0
drift_samples = 0


def set_balance(value):
    robot.settings["balance"] = round(max(-TRIM_LIMIT, min(TRIM_LIMIT, value)), 3)
    save(robot.settings)


while True:
    now = explorer.ticks()
    balance = robot.settings["balance"]

    if SELECT.pressed:
        robot.stop()
        if driving:
            driving = False
        else:
            if heading is not None:
                heading.settle()
            driving = True
            drift_total = 0.0
            drift_samples = 0
            run_started = explorer.ticks()
            now = run_started
    if not driving:
        if UP.pressed:
            set_balance(balance - TRIM_STEP)
        if DOWN.pressed:
            set_balance(balance + TRIM_STEP)
        if button_c.pressed:
            set_balance(0.0)
        if button_z.pressed and drift is not None:
            set_balance(balance + max(-AUTO_LIMIT, min(AUTO_LIMIT, drift * AUTO_GAIN)))
            drift = None

    if driving:
        if heading is not None:
            heading.update()
            if now - run_started >= WARMUP_MS:
                drift_total += heading.rate
                drift_samples += 1
        if now - run_started >= RUN_MS:
            driving = False
            robot.stop()
            if drift_samples:
                drift = drift_total / drift_samples
        else:
            robot.drive(1, 1)

    screen.pen = INK
    screen.clear()

    screen.font = TITLE_FONT
    screen.pen = PAPER
    screen.text("Drive straight", 16, 12, 26)
    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text("Put the robot on the floor with room ahead. A drives for 3 seconds.", rect(16, 44, 288, 40), 14)

    balance = robot.settings["balance"]
    centre = 160
    span = 140
    screen.pen = FAINT
    screen.shape(shape.rounded_rectangle(centre - span, 100, span * 2, 14, 7))
    screen.pen = PAPER
    screen.shape(shape.rectangle(centre - 1, 94, 2, 26))
    screen.pen = ACCENT
    screen.shape(shape.circle(centre + span * balance / TRIM_LIMIT, 107, 10))
    screen.pen = DIM
    screen.text("left", 20, 122, 12)
    screen.text("right", rect(20, 122, 280, 14), 12, align=(image.RIGHT, image.TOP))
    screen.font = TITLE_FONT
    screen.pen = PAPER
    screen.text(f"Trim {balance * 100:+.0f}", rect(0, 136, 320, 26), 20, align=(image.CENTER, image.MIDDLE))

    screen.font = BODY_FONT
    if driving:
        screen.pen = ACCENT
        screen.text("Driving...", rect(0, 166, 320, 20), 16, align=(image.CENTER, image.MIDDLE))
    elif drift is not None:
        if abs(drift) < STRAIGHT_DPS:
            message = "Straight!"
        else:
            message = f"Veered {'left' if drift > 0 else 'right'} {abs(drift):.1f} deg/s.  Z  Fix it"
        screen.pen = ACCENT if abs(drift) < STRAIGHT_DPS else ALERT
        screen.text(message, rect(0, 166, 320, 20), 16, align=(image.CENTER, image.MIDDLE))
    elif heading is None:
        screen.pen = DIM
        screen.text("Plug in the sensor stick for auto trim", rect(0, 166, 320, 20), 13, align=(image.CENTER, image.MIDDLE))

    screen.pen = DIM
    screen.text("A  Drive    X Y  Steer left / right    C  Reset", 12, 214, 13)

    explorer.update()

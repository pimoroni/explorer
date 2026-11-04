"""Calibrate
Set up your robot so it drives straight.

You will need:
- 2 servos with wheels
- Battery holder
- Multi-Sensor Stick, for auto setup

Icon: tune
"""
import explorer
from explorer import BACK, DOWN, SELECT, UP, button_c, button_z, screen, stick, wiring
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

SPIN_MS = 1000
DIRECTION_MS = 1000
STRAIGHT_MS = 4000
WARMUP_MS = 400
SPIN_MIN_DEGREES = 20
TRIM_STEP = 0.01
TRIM_LIMIT = 0.5
AUTO_GAIN = 0.003
AUTO_LIMIT = 0.05
STRAIGHT_DEGREES = 5

SPIN, DIRECTION, STRAIGHT = range(3)
TITLES = ("Spin", "Direction", "Drive straight")
READY, RUNNING, ASK, DONE = range(4)

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

stage = SPIN
phase = READY
run_started = 0
message = ""
message_good = True
drift = None
drift_total = 0.0
drift_samples = 0


def update_setting(name, value):
    robot.settings[name] = value
    save(robot.settings)


def set_balance(value):
    update_setting("balance", round(max(-TRIM_LIMIT, min(TRIM_LIMIT, value)), 3))


def veer():
    return drift * (STRAIGHT_MS - WARMUP_MS) / 1000


def run_ms():
    return (SPIN_MS, DIRECTION_MS, STRAIGHT_MS)[stage]


def start_run():
    global phase, run_started, drift_total, drift_samples, message
    robot.stop()
    if heading is not None:
        heading.settle()
    phase = RUNNING
    message = ""
    drift_total = 0.0
    drift_samples = 0
    run_started = explorer.ticks()


def finish_run():
    global phase, message, message_good, drift
    robot.stop()
    if stage == SPIN and heading is not None:
        turned = heading.heading
        if abs(turned) < SPIN_MIN_DEGREES:
            phase, message, message_good = DONE, "It hardly turned. Check the servos and battery, then A to try again.", False
        elif turned > 0:
            update_setting("flip", not robot.settings["flip"])
            phase, message, message_good = DONE, "It spun left, so the servo direction is now flipped. A to check again.", False
        else:
            phase, message, message_good = DONE, "Spun right. All good!", True
    elif stage == STRAIGHT:
        phase = DONE
        drift = drift_total / drift_samples if drift_samples else None
    else:
        phase = ASK


def answer(yes):
    global stage, phase, message, message_good
    if yes:
        stage, phase, message = stage + 1, READY, ""
        return
    if stage == SPIN:
        update_setting("flip", not robot.settings["flip"])
    else:
        update_setting("swapped", not robot.settings["swapped"])
    phase, message, message_good = READY, "Changed. A to check again.", False


while True:
    now = explorer.ticks()

    if phase == RUNNING:
        if heading is not None:
            heading.update()
            if now - run_started >= WARMUP_MS:
                drift_total += heading.rate
                drift_samples += 1
        if SELECT.pressed or now - run_started >= run_ms():
            finish_run()
        elif stage == SPIN:
            robot.drive(1, -1)
        else:
            robot.drive(1, 1)
    elif phase == ASK:
        if SELECT.pressed:
            answer(True)
        elif UP.pressed:
            answer(False)
    else:
        if SELECT.pressed:
            start_run()
        if button_c.pressed and stage > SPIN:
            stage, phase, message = stage - 1, READY, ""
        if button_z.pressed and stage < STRAIGHT:
            stage, phase, message = stage + 1, READY, ""
        if stage == STRAIGHT:
            if UP.pressed:
                set_balance(robot.settings["balance"] - TRIM_STEP)
            if DOWN.pressed:
                set_balance(robot.settings["balance"] + TRIM_STEP)
            if BACK.pressed and drift is not None and abs(veer()) >= STRAIGHT_DEGREES:
                set_balance(robot.settings["balance"] + max(-AUTO_LIMIT, min(AUTO_LIMIT, drift * AUTO_GAIN)))
                drift = None

    screen.pen = INK
    screen.clear()

    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text(f"Step {stage + 1} of 3", 16, 8, 13)
    screen.font = TITLE_FONT
    screen.pen = PAPER
    screen.text(TITLES[stage], 16, 22, 26)

    if stage == SPIN:
        instructions = "Put the robot on the floor. A spins it on the spot for a second."
        question = "Did it spin right (clockwise)?"
    elif stage == DIRECTION:
        instructions = "Room ahead of the robot? A drives it for a second."
        question = "Did it drive forwards?"
    else:
        instructions = "Room ahead of the robot? A drives it for 4 seconds."
        question = ""
    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text(instructions, rect(16, 56, 288, 40), 14)

    if stage == STRAIGHT:
        balance = robot.settings["balance"]
        centre = 160
        span = 140
        screen.pen = FAINT
        screen.shape(shape.rounded_rectangle(centre - span, 104, span * 2, 14, 7))
        screen.pen = PAPER
        screen.shape(shape.rectangle(centre - 1, 98, 2, 26))
        screen.pen = ACCENT
        screen.shape(shape.circle(centre + span * balance / TRIM_LIMIT, 111, 10))
        screen.pen = DIM
        screen.text("left", 20, 126, 12)
        screen.text("right", rect(20, 126, 280, 14), 12, align=(image.RIGHT, image.TOP))
        screen.font = TITLE_FONT
        screen.pen = PAPER
        screen.text(f"Trim {balance * 100:+.0f}", rect(0, 140, 320, 26), 20, align=(image.CENTER, image.MIDDLE))

    screen.font = BODY_FONT
    if phase == RUNNING:
        screen.pen = ACCENT
        screen.text("Running...", rect(16, 168, 288, 20), 16)
    elif phase == ASK:
        screen.pen = PAPER
        screen.text(question, rect(16, 120, 288, 24), 18)
        screen.pen = DIM
        screen.text("A  Yes    X  No", rect(16, 150, 288, 20), 16)
    elif stage == STRAIGHT and phase == DONE and drift is not None:
        straight = abs(veer()) < STRAIGHT_DEGREES
        screen.pen = ACCENT if straight else ALERT
        text = "Straight enough!" if straight else f"Veered {'left' if drift > 0 else 'right'} {abs(veer()):.0f} degrees.  B  Fix it"
        screen.text(text, rect(16, 168, 288, 20), 15)
    elif message:
        screen.pen = ACCENT if message_good else ALERT
        screen.text(message, rect(16, 120, 288, 44), 15)
    elif stage == STRAIGHT and heading is None:
        screen.pen = DIM
        screen.text("Plug in the sensor stick for auto trim", rect(16, 168, 288, 20), 13)

    screen.pen = DIM
    if phase == ASK:
        hint = ""
    elif stage == STRAIGHT:
        hint = "A  Drive   X Y  Steer left / right   C  Back"
    else:
        hint = "A  Test    C Z  Previous / next step"
    screen.text(hint, 12, 214, 13)

    explorer.update()

"""Calibrate
Set up your robot so it drives straight.

You will need:
- 2 servos with wheels
- Battery holder
- Multi-Sensor Stick, for auto setup

Icon: tune
"""
import machine

import explorer
from explorer import BACK, DOWN, SELECT, UP, button_c, button_z, labels, screen, stick, wiring
from explorer.robot import LEFT_SERVO, RIGHT_SERVO, Heading, Robot, hands_off, save
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
        hands_off(explorer, TITLE_FONT, heading)
        if stage == SPIN:
            update_setting("level", list(heading.measured_up))
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
            phase, message, message_good = DONE, "It hardly turned. Check the servos and battery.", False
        elif turned > 0:
            update_setting("flip", not robot.settings["flip"])
            phase, message, message_good = DONE, "It spun left, so the servo direction is now flipped. Spin again to check.", False
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
    phase, message, message_good = READY, "Changed. Try again to check.", False


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
        elif BACK.pressed:
            answer(False)
    else:
        veered = stage == STRAIGHT and phase == DONE and drift is not None and abs(veer()) >= STRAIGHT_DEGREES
        if SELECT.pressed:
            start_run()
        elif BACK.pressed and stage > SPIN:
            stage, phase, message = stage - 1, READY, ""
        elif UP.pressed:
            if stage == STRAIGHT:
                robot.stop()
                machine.reset()
            stage, phase, message = stage + 1, READY, ""
        elif stage == STRAIGHT:
            if button_c.pressed:
                set_balance(robot.settings["balance"] - TRIM_STEP)
            if button_z.pressed:
                set_balance(robot.settings["balance"] + TRIM_STEP)
            if DOWN.pressed and veered:
                set_balance(robot.settings["balance"] + max(-AUTO_LIMIT, min(AUTO_LIMIT, drift * AUTO_GAIN)))
                drift = None

    screen.pen = INK
    screen.clear()

    screen.font = TITLE_FONT
    screen.pen = PAPER
    screen.text(TITLES[stage], 12, 2, 24)
    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text(f"Step {stage + 1} of 3", rect(0, 8, 308, 20), 16, align=(image.RIGHT, image.TOP))

    if stage == SPIN:
        instructions = "Robot on a flat floor. It spins on the spot for a second."
        question = "Did it spin right?"
    elif stage == DIRECTION:
        instructions = "Room ahead? It drives for a second."
        question = "Did it drive forwards?"
    else:
        instructions = "Room ahead? It drives for 4 seconds."
        question = ""
    screen.text(instructions, rect(12, 64, 296, 42), 17)

    if stage == STRAIGHT:
        balance = robot.settings["balance"]
        span = 100
        screen.pen = FAINT
        screen.shape(shape.rounded_rectangle(160 - span, 150, span * 2, 12, 6))
        screen.pen = PAPER
        screen.shape(shape.rectangle(159, 144, 2, 24))
        screen.pen = ACCENT
        screen.shape(shape.circle(160 + span * balance / TRIM_LIMIT, 156, 10))
        screen.font = TITLE_FONT
        screen.pen = PAPER
        screen.text(f"Trim {balance * 100:+.0f}", rect(80, 106, 160, 28), 22, align=(image.CENTER, image.MIDDLE))

    status = ""
    status_pen = DIM
    highlight = None
    if phase == RUNNING:
        status, status_pen = "Running...", ACCENT
        actions = {"A": "Stop"}
    elif phase == ASK:
        screen.font = TITLE_FONT
        screen.pen = PAPER
        screen.text(question, rect(12, 134, 296, 36), 22, align=(image.CENTER, image.MIDDLE))
        actions = {"A": "Yes", "B": "No"}
    else:
        actions = {"A": "Drive" if stage else "Spin"}
        highlight = "A"
        if stage > SPIN:
            actions["B"] = "Back"
        if stage < STRAIGHT:
            actions["X"] = "Next"
            if message:
                status, status_pen = message, ACCENT if message_good else ALERT
                if message_good:
                    highlight = "X"
        else:
            actions["X"] = "Done"
            actions["C"] = "Left"
            actions["Z"] = "Right"
            if phase == DONE and drift is not None:
                straight = abs(veer()) < STRAIGHT_DEGREES
                status = "Straight enough!" if straight else f"Veered {'left' if drift > 0 else 'right'} {abs(veer()):.0f} degrees"
                status_pen = ACCENT if straight else ALERT
                if straight:
                    highlight = "X"
                else:
                    actions["Y"] = "Fix"
                    highlight = "Y"
            elif heading is None:
                status = "Plug in the sensor stick for auto trim"
    if status:
        screen.font = BODY_FONT
        screen.pen = status_pen
        screen.text(status, rect(12, 208, 296, 32) if stage == STRAIGHT or phase == RUNNING else rect(12, 128, 296, 44), 17, align=(image.CENTER, image.MIDDLE))

    labels.draw(screen, TITLE_FONT, actions, highlight)

    explorer.update()

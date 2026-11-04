"""Bump Bot
A robot that backs away from walls.

You will need:
- 2 servos with wheels
- Multi-Sensor Stick
- Battery holder

Icon: smart_toy
"""
import random

import explorer
from breakout_ltr559 import BreakoutLTR559
from explorer import DOWN, SELECT, UP, labels, screen, wiring
from explorer.robot import LEFT_SERVO, RIGHT_SERVO, Heading, Robot, hands_off
from lsm6ds3 import LSM6DS3
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")


def proximity_sensor(bus):
    sensor = BreakoutLTR559(bus)
    sensor.proximity_led(100, 100, 30, 8)
    sensor.proximity_measurement_rate(50)
    return sensor


INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)
GO = color.rgb(52, 199, 138)
ALERT = color.rgb(255, 122, 61)

BACK_MS = 700
TURN_TIMEOUT_MS = 2500
PROXIMITY_MAX = 400
THRESHOLD_STEP = 10
TILT_LIMIT = 8

WIRING = (
    (
        "Left wheel servo on header 1, right on 2. Brown wire to GND, on the right.",
        (wiring.servo(LEFT_SERVO), wiring.servo(RIGHT_SERVO)),
    ),
)

wiring.show(WIRING, TITLE_FONT, BODY_FONT)
robot = Robot(explorer)
ltr = explorer.sensor(proximity_sensor, TITLE_FONT, on_disconnect=robot.stop)
imu = explorer.sensor(LSM6DS3, TITLE_FONT, on_disconnect=robot.stop)
heading = Heading(imu, robot.settings["level"])
heading.settle()

STOPPED, DRIVING, BACKING, TURNING = range(4)
LABELS = ("Stopped", "Driving", "Backing up", "Turning")
state = STOPPED
state_started = 0
turn = 1
turn_angle = 90
turn_from = 0.0
threshold = 40
proximity = 0
dodges = 0
reason = ""

while True:
    now = explorer.ticks()
    reading = ltr.get_reading()
    if reading is not None:
        proximity = reading[BreakoutLTR559.PROXIMITY]
    heading.update()

    if UP.pressed:
        threshold = max(THRESHOLD_STEP, threshold - THRESHOLD_STEP)
    if DOWN.pressed:
        threshold = min(PROXIMITY_MAX - THRESHOLD_STEP, threshold + THRESHOLD_STEP)
    if SELECT.pressed:
        robot.stop()
        if state == STOPPED:
            hands_off(explorer, TITLE_FONT, heading)
            state = DRIVING
        else:
            state = STOPPED

    seen = proximity > threshold
    bumped = heading.tilt > TILT_LIMIT
    if state == DRIVING and (seen or bumped):
        state, state_started = BACKING, now
        reason = "Bumped!" if bumped else "Spotted something"
        dodges += 1
        explorer.beep(220 if bumped else 440, 150)
    elif state == BACKING and now - state_started >= BACK_MS:
        turn = random.choice((-1, 1))
        turn_angle = random.randint(70, 150)
        turn_from = heading.heading
        state, state_started = TURNING, now
    elif state == TURNING and (abs(heading.heading - turn_from) >= turn_angle or now - state_started >= TURN_TIMEOUT_MS):
        state = DRIVING

    if state == DRIVING:
        robot.drive(1, 1)
    elif state == BACKING:
        robot.drive(-1, -1)
    elif state == TURNING:
        robot.drive(turn, -turn)
    else:
        robot.stop()

    screen.pen = INK
    screen.clear()

    screen.font = TITLE_FONT
    screen.pen = ALERT if state in (BACKING, TURNING) else GO if state == DRIVING else PAPER
    screen.text(LABELS[state], 12, 0, 26)
    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text(f"Dodged {dodges} obstacle{'' if dodges == 1 else 's'}", 12, 64, 18)
    if reason:
        screen.text(f"Last: {reason}", 12, 86, 16)

    level = min(1.0, proximity / PROXIMITY_MAX)
    marker = 16 + 288 * threshold / PROXIMITY_MAX
    screen.pen = FAINT
    screen.shape(shape.rounded_rectangle(16, 142, 288, 14, 7))
    screen.pen = ALERT if seen else GO
    screen.shape(shape.rounded_rectangle(16, 142, 14 + 274 * level, 14, 7))
    screen.pen = PAPER
    screen.shape(shape.rectangle(marker - 1, 136, 3, 26))
    screen.pen = DIM
    screen.text("Reacts at", 12, 110, 16)
    screen.text("Far", 16, 160, 14)
    screen.text("Near", rect(16, 160, 288, 16), 14, align=(image.RIGHT, image.TOP))
    screen.pen = ALERT if bumped else DIM
    screen.text(f"Tilt {heading.tilt:.0f}°", 12, 182, 16)
    if not robot.settings["level"]:
        screen.pen = DIM
        screen.text("Run Calibrate to set level", 12, 212, 16)

    actions = {"A": "Go" if state == STOPPED else "Stop"}
    if threshold > THRESHOLD_STEP:
        actions["X"] = "Further"
    if threshold < PROXIMITY_MAX - THRESHOLD_STEP:
        actions["Y"] = "Nearer"
    labels.draw(screen, TITLE_FONT, actions, "A" if state == STOPPED else None)

    explorer.update()

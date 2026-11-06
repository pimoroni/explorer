"""Turtle
Program a path, then watch your robot drive it.

You will need:
- 2 servos with wheels
- Battery holder
- Multi-Sensor Stick, for accurate turns

Icon: route
"""
import math
from array import array

import explorer
from explorer import BACK, SELECT, UP, button_c, button_z, labels, screen, stick, wiring
from explorer.robot import LEFT_SERVO, RIGHT_SERVO, Heading, Robot, hands_off
from lsm6ds3 import LSM6DS3
from picovector import color, font, image, mat3, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)
PATH = color.rgb(52, 199, 138)
TURTLE = color.rgb(255, 204, 51)

FORWARD_MS = 1000
TURN_MS_PER_90 = 550
TURN_STEP = 45
TURN_TOLERANCE = 2
TURN_TIMEOUT_MS = 4000
TURN_SLOWDOWN = 45
TURN_MIN = 0.35
STEER_GAIN = 0.03
STEER_MAX = 0.4
PAUSE_MS = 250
MAX_MOVES = 16
TILE = 30
TILE_GAP = 3
TILES_X = 64
TILES_Y = 36
PANEL = (202, 62, 110, 112)

WIRING = (
    (
        "Left wheel servo on header 1, right on 2. Brown wire to GND, on the right.",
        (wiring.servo(LEFT_SERVO), wiring.servo(RIGHT_SERVO)),
    ),
)

wiring.show(WIRING, TITLE_FONT, BODY_FONT)
explorer.rotate(True)

robot = Robot(explorer)
heading = None
if stick.connected(explorer.i2c()):
    heading = Heading(explorer.sensor(LSM6DS3, TITLE_FONT, on_disconnect=robot.stop), robot.settings["level"])

program = ["F", 90, "F", 90, "F", 90, "F", 90]
running = False
step = 0
step_started = 0
step_active = False
resume_at = 0
target = 0.0
turned_from = 0.0


def add_turn(degrees):
    if program and program[-1] != "F":
        total = (program[-1] + degrees + 180) % 360 - 180
        if total == -180 and degrees > 0:
            total = 180
        if total:
            program[-1] = total
        else:
            program.pop()
    elif len(program) < MAX_MOVES:
        program.append(degrees)


def move_ms(move):
    return FORWARD_MS if move == "F" else TURN_MS_PER_90 * abs(move) / 90


def run_step(move, elapsed):
    if heading is None:
        if elapsed >= move_ms(move):
            return True
        if move == "F":
            robot.drive(1, 1)
        else:
            direction = 1 if move > 0 else -1
            robot.drive(direction, -direction)
        return False

    error = target - heading.heading
    if move == "F":
        if elapsed >= FORWARD_MS:
            return True
        steer = max(-STEER_MAX, min(STEER_MAX, error * STEER_GAIN))
        robot.drive(1 - steer, 1 + steer)
        return False
    if abs(error) <= TURN_TOLERANCE or elapsed >= TURN_TIMEOUT_MS:
        return True
    power = max(TURN_MIN, min(1.0, abs(error) / TURN_SLOWDOWN))
    direction = -1 if error > 0 else 1
    robot.drive(direction * power, -direction * power)
    return False


def step_progress(move, elapsed):
    if heading is None or move == "F":
        return min(1.0, elapsed / move_ms(move))
    return max(0.0, min(1.0, abs(heading.heading - turned_from) / abs(move)))


def trace(moves, progress=None):
    x = y = 0.0
    angle = 0
    points = [(x, y)]
    for index, move in enumerate(moves):
        amount = 1.0 if progress is None or index < progress[0] else progress[1] if index == progress[0] else 0.0
        if move == "F":
            x += math.sin(math.radians(angle)) * amount
            y -= math.cos(math.radians(angle)) * amount
            points.append((x, y))
        else:
            angle += move * amount
    return points, angle


def draw_arrow(angle, x, y, size, pen):
    arrow = shape.custom(array("f", (0, -size, size * 0.8, size * 0.1, size * 0.3, size * 0.1, size * 0.3, size, -size * 0.3, size, -size * 0.3, size * 0.1, -size * 0.8, size * 0.1)))
    arrow.transform = mat3().translate(x, y).rotate(angle)
    screen.pen = pen
    screen.shape(arrow)


def draw_path(points, angle):
    px, py, width, height = PANEL
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 2)
    scale = min(width, height) * 0.8 / span
    middle_x = (max(xs) + min(xs)) / 2
    middle_y = (max(ys) + min(ys)) / 2

    def place(x, y):
        return px + width / 2 + (x - middle_x) * scale, py + height / 2 + (y - middle_y) * scale

    screen.pen = PATH
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        ax, ay = place(x1, y1)
        bx, by = place(x2, y2)
        screen.shape(shape.line(ax, ay, bx, by, 4))
    tx, ty = place(*points[-1])
    turtle = shape.custom(array("f", (0, -10, 8, 8, 0, 4, -8, 8)))
    turtle.transform = mat3().translate(tx, ty).rotate(angle)
    screen.pen = TURTLE
    screen.shape(turtle)


def start_step(now):
    global step_started, step_active, target, turned_from
    step_started = now
    step_active = True
    move = program[step]
    if heading is not None:
        turned_from = heading.heading
        if move != "F":
            target -= move


while True:
    now = explorer.ticks()
    if heading is not None:
        heading.update()

    if running:
        if now < resume_at:
            robot.stop()
        else:
            if not step_active:
                start_step(now)
            if run_step(program[step], now - step_started):
                robot.stop()
                step += 1
                step_active = False
                resume_at = now + PAUSE_MS
                if step >= len(program):
                    running = False
        if SELECT.pressed or BACK.pressed:
            running = False
            robot.stop()
    else:
        if UP.pressed and len(program) < MAX_MOVES:
            program.append("F")
        if button_c.pressed:
            add_turn(-TURN_STEP)
        if button_z.pressed:
            add_turn(TURN_STEP)
        if BACK.pressed and program:
            program.pop()
        if SELECT.pressed and program:
            if heading is not None:
                hands_off(explorer, TITLE_FONT, heading)
            running = True
            step = 0
            step_active = False
            resume_at = 0
            target = 0.0
            explorer.beep(880, 60)

    screen.pen = INK
    screen.clear()

    for index, move in enumerate(program):
        x = TILES_X + TILE / 2 + (index % 4) * (TILE + TILE_GAP)
        y = TILES_Y + TILE / 2 + (index // 4) * (TILE + TILE_GAP)
        current = running and index == step
        screen.pen = PAPER if current else FAINT
        screen.shape(shape.rounded_rectangle(x - TILE / 2, y - TILE / 2, TILE, TILE, 6))
        if move == "F":
            draw_arrow(0, x, y, 10, INK if current else PAPER)
        else:
            draw_arrow(move, x, y - 7, 6, INK if current else PAPER)
            screen.font = BODY_FONT
            screen.pen = INK if current else DIM
            screen.text(f"{abs(move)}", rect(x - TILE / 2, y, TILE, 14), 14, align=(image.CENTER, image.TOP))

    screen.pen = FAINT
    screen.shape(shape.rounded_rectangle(*PANEL, 12))
    progress = None
    if running:
        progress = (step, step_progress(program[step], now - step_started) if step_active else 0.0)
    draw_path(*trace(program, progress))

    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text(f"{len(program)}/{MAX_MOVES} moves", 12, 212, 16)
    screen.text("Gyro turns" if heading is not None else "Timed turns", rect(12, 212, 296, 20), 16, align=(image.RIGHT, image.TOP))

    if running:
        actions = {"A": "Stop"}
    else:
        actions = {}
        if program:
            actions["A"] = "Go"
            actions["B"] = "Undo"
        actions["C"] = labels.LEFT
        actions["Z"] = labels.RIGHT
        if len(program) < MAX_MOVES:
            actions["X"] = labels.UP
    labels.draw(screen, TITLE_FONT, actions, None if running else "A")

    explorer.update()

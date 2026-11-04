import gc
import math
import time
from array import array

from picovector import color, image, mat3, rect, shape

from . import labels

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
SILK = color.rgb(250, 246, 238)
BOARD = color.rgb(34, 58, 102)
HEADER = color.rgb(18, 18, 20)
HOLE = color.rgb(4, 4, 4)
BREADBOARD = color.rgb(26, 26, 28)
GROOVE = color.rgb(14, 14, 16)
CLIP = color.rgb(176, 176, 182)
BEVEL = color.rgb(44, 44, 48)
WIRE_SHINE = color.rgb(120, 118, 112)

BLACK = (10, 10, 10)
RED = (220, 50, 40)
BROWN = (130, 74, 40)
GREY = (128, 128, 132)

PITCH = 13
COLUMNS = 17
LEFT_COLUMN_X = 13
BOTTOM_Y = 154
GROOVE_GAP = PITCH * 3
SOCKET_X = LEFT_COLUMN_X + (COLUMNS - 1) * PITCH + 52
RIGHT_SOCKET_X = SOCKET_X + PITCH
PANEL_TOP = 50
LEFT_LABELS = ("GP0", "GP1", "GP2", "GP3", "GP4", "GP5")
RIGHT_LABELS = ("ADC0", "ADC1", "ADC2", "3.3V", "GND", "GND")
SERVO_X = SOCKET_X - PITCH / 2
SERVO_TOP = 78
SERVO_LABELS = ("SIG", "5V", "GND")
SERVO_WIRES = ((255, 140, 30), RED, BROWN)

LED_BASE = 8
LED_RADIUS = 5
BUTTON_SIZE = 58
BUTTON_CAP = 17
POT_WIDTH = 44
POT_HEIGHT = 34
POT_SHAFT = 18
RGB_LED_BASE = 14
RGB_LED_RADIUS = 8
RGB_LED_LABELS = ("R", "-", "G", "B")

PLACE_MS = 600
PART_GAP_MS = 250
STEP_HOLD_MS = 1200
END_HOLD_MS = 1600
DROP_HEIGHT = 30


def hole(column, row, top=False):
    x = LEFT_COLUMN_X + column * PITCH
    if top:
        return (x, BOTTOM_Y - GROOVE_GAP - (4 - row) * PITCH, (column, True))
    return (x, BOTTOM_Y + row * PITCH, (column, False))


def gpio(number):
    return (SOCKET_X, BOTTOM_Y + number * PITCH, None)


def ground(row=4):
    return (RIGHT_SOCKET_X, BOTTOM_Y + row * PITCH, None)


def adc(number):
    return (RIGHT_SOCKET_X, BOTTOM_Y + number * PITCH, None)


def power():
    return (RIGHT_SOCKET_X, BOTTOM_Y + 3 * PITCH, None)


def led(row, rgb):
    return ("led", hole(COLUMNS - 1, row), gpio(row), rgb, 0.25, 1)


def led_across(column, rgb):
    return ("led", hole(column, 0), hole(column, 4, True), rgb, 0.5, -1)


def wire(start, end, rgb, start_bend=(0, 30), end_bend=(0, 30)):
    return ("wire", start, end, rgb, start_bend, end_bend)


def button(column, top_row=3, bottom_row=1):
    return ("button", hole(column, top_row, True), hole(column + 2, bottom_row))


def rgb_led(column, row=1):
    return ("rgb", tuple(hole(column + offset, row) for offset in range(4)))


def potentiometer(column, row=4):
    return ("pot", tuple(hole(column + offset, row, True) for offset in range(3)))


def servo(number):
    return ("servo", number)


def _part_strips(part):
    kind = part[0]
    if kind == "servo":
        return ()
    if kind in ("rgb", "pot"):
        return tuple(leg[2] for leg in part[1])
    if kind == "led":
        return (part[1][2],)
    if kind == "wire":
        return tuple(end[2] for end in part[1:3] if end[2])
    left, right = part[1], part[2]
    return (left[2], (right[2][0], True), (left[2][0], False), right[2])


def _ease(t):
    return 1 - (1 - t) * (1 - t) * (1 - t)


def _stroke(points, width):
    flat = array("f")
    for x, y in points:
        flat.append(x)
        flat.append(y)
    return shape.custom(flat).stroke(width, shape.PATH_OPEN | shape.JOIN_ROUND | shape.CAP_ROUND)


def _wire_path(part):
    _, start, end, _, start_bend, end_bend = part
    x0, y0 = start[0], start[1]
    x3, y3 = end[0], end[1]
    c1x, c1y = x0 + start_bend[0], y0 + start_bend[1]
    c2x, c2y = x3 + end_bend[0], y3 + end_bend[1]
    path = []
    for step in range(25):
        t = step / 24
        u = 1 - t
        path.append((
            u * u * u * x0 + 3 * u * u * t * c1x + 3 * u * t * t * c2x + t * t * t * x3,
            u * u * u * y0 + 3 * u * u * t * c1y + 3 * u * t * t * c2y + t * t * t * y3,
        ))
    return path


def _draw_board(screen, strips):
    screen.pen = BOARD
    screen.shape(shape.rounded_rectangle(4, PANEL_TOP, 312, 236 - PANEL_TOP, 8))

    left = LEFT_COLUMN_X - 9
    right = LEFT_COLUMN_X + (COLUMNS - 1) * PITCH + 9
    top = BOTTOM_Y - GROOVE_GAP - 4 * PITCH - 9
    bottom = BOTTOM_Y + 4 * PITCH + 9
    screen.pen = BREADBOARD
    screen.shape(shape.rounded_rectangle(left, top, right - left, bottom - top, 3))
    groove_y = BOTTOM_Y - GROOVE_GAP / 2
    screen.pen = GROOVE
    screen.shape(shape.rounded_rectangle(left + 26, groove_y - 6, right - left - 52, 12, 4))

    for column, upper in strips:
        x, y, _ = hole(column, 0, upper)
        screen.pen = CLIP
        screen.shape(shape.rectangle(x - 4, y - 5, 8, PITCH * 4 + 10))

    for column in range(COLUMNS):
        for row in range(5):
            for upper in (True, False):
                x, y, strip = hole(column, row, upper)
                screen.pen = BEVEL
                screen.shape(shape.rectangle(x - 4, y - 4, 8, 8))
                screen.pen = CLIP if strip in strips else HOLE
                screen.shape(shape.rectangle(x - 2, y - 2, 4, 4))

    screen.pen = HEADER
    screen.shape(shape.rectangle(SOCKET_X - 9, BOTTOM_Y - 9, PITCH + 18, PITCH * 5 + 18))
    for row in range(6):
        y = BOTTOM_Y + row * PITCH
        screen.pen = HOLE
        screen.shape(shape.rectangle(SOCKET_X - 4, y - 4, 8, 8))
        screen.shape(shape.rectangle(RIGHT_SOCKET_X - 4, y - 4, 8, 8))
        screen.pen = SILK
        screen.text(LEFT_LABELS[row], SOCKET_X - 21, y - 1, 7)
        screen.text(RIGHT_LABELS[row], RIGHT_SOCKET_X + 8, y - 5, 7)
    screen.text("GPIO", SOCKET_X - 3, BOTTOM_Y - 27, 10)

    for row in range(4):
        y = SERVO_TOP + row * PITCH
        screen.pen = HEADER
        screen.shape(shape.rounded_rectangle(SERVO_X - 7, y - 6, PITCH * 2 + 14, 12, 2))
        screen.pen = CLIP
        for pin in range(3):
            screen.shape(shape.rectangle(SERVO_X + pin * PITCH - 1.5, y - 1.5, 3, 3))
        screen.pen = SILK
        screen.text(str(row + 1), SERVO_X - 16, y - 6, 9)
    for pin, label in enumerate(SERVO_LABELS):
        x = SERVO_X + pin * PITCH - 4
        y = SERVO_TOP - 9
        if pin:
            screen.pen = SILK
            screen.shape(shape.rectangle(x - 1, y - 18, 10, 19))
            screen.pen = BOARD
        else:
            screen.pen = SILK
        screen.text(label, x, y, 7, transform=mat3().translate(x, y).rotate(-90).translate(-x, -y))


def _quad(base, along, normal, a0, a1, b0, b1):
    points = array("f")
    for a, b in ((a0, b0), (a1, b0), (a1, b1), (a0, b1)):
        points.append(base[0] + along[0] * a + normal[0] * b)
        points.append(base[1] + along[1] * a + normal[1] * b)
    return shape.custom(points)


def _draw_led(screen, part, drop, alpha):
    _, minus, plus, (r, g, b), position, side = part
    minus_x, minus_y = minus[0], minus[1] - drop
    plus_x, plus_y = plus[0], plus[1] - drop
    length = math.sqrt((plus_x - minus_x) ** 2 + (plus_y - minus_y) ** 2)
    along = ((plus_x - minus_x) / length, (plus_y - minus_y) / length)
    normal = (along[1] * side, -along[0] * side)
    base = (
        minus_x + along[0] * length * position + normal[0] * LED_BASE,
        minus_y + along[1] * length * position + normal[1] * LED_BASE,
    )

    def point(a, b):
        return (base[0] + along[0] * a + normal[0] * b, base[1] + along[1] * a + normal[1] * b)

    screen.pen = color.rgb(196, 196, 202, alpha)
    screen.shape(_stroke((point(-2.5, 0), (minus_x, minus_y)), 1.4))
    screen.shape(_stroke((point(2.5, 0), (plus_x, plus_y)), 1.4))
    screen.pen = color.rgb(r * 3 // 5, g * 3 // 5, b * 3 // 5, alpha)
    screen.shape(_quad(base, along, normal, -5, 8, 0, 3))
    screen.pen = color.rgb(r, g, b, alpha)
    screen.shape(_quad(base, along, normal, -LED_RADIUS, LED_RADIUS, 2, 11))
    dome_x, dome_y = point(0, 11)
    screen.shape(shape.circle(dome_x, dome_y, LED_RADIUS))
    screen.pen = color.rgb(255, 255, 255, alpha * 2 // 3)
    screen.shape(_quad(base, along, normal, -3.5, -1.5, 5, 13))
    screen.pen = color.rgb(239, 235, 227, alpha)
    for sign, a in (("-", -9), ("+", 9)):
        x, y = point(a, 13)
        screen.text(sign, x - 3, y - 7, 10)


def _draw_rgb_led(screen, part, drop, alpha):
    legs = part[1]
    centre = (legs[0][0] + legs[-1][0]) / 2
    base = legs[0][1] - drop - RGB_LED_BASE
    screen.pen = color.rgb(196, 196, 202, alpha)
    for index, leg in enumerate(legs):
        screen.shape(_stroke(((centre + (index - 1.5) * 3, base), (leg[0], leg[1] - drop)), 1.4))
    screen.pen = color.rgb(200, 200, 206, alpha)
    screen.shape(shape.rectangle(centre - RGB_LED_RADIUS - 2, base - 3, RGB_LED_RADIUS * 2 + 4, 3))
    screen.pen = color.rgb(236, 236, 240, alpha)
    screen.shape(shape.rectangle(centre - RGB_LED_RADIUS, base - 14, RGB_LED_RADIUS * 2, 12))
    screen.shape(shape.circle(centre, base - 14, RGB_LED_RADIUS))
    for index, rgb in enumerate(((235, 60, 50), (60, 200, 90), (70, 120, 255))):
        screen.pen = color.rgb(*rgb, alpha // 2)
        screen.shape(shape.circle(centre + (index - 1) * 4, base - 10, 2.5))
    for label, leg in zip(RGB_LED_LABELS, legs):
        label_y = leg[1] - drop + PITCH / 2 + 2
        screen.pen = color.rgb(14, 14, 16, alpha)
        screen.shape(shape.rounded_rectangle(leg[0] - 5, label_y - 6, 10, 12, 2))
        screen.pen = color.rgb(239, 235, 227, alpha)
        screen.text(label, leg[0] - 3, label_y - 6, 9)


def _draw_potentiometer(screen, part, drop, alpha):
    legs = part[1]
    centre_x = legs[1][0]
    top = legs[0][1] - drop + 3
    screen.pen = color.rgb(196, 196, 202, alpha)
    for leg in legs:
        screen.shape(_stroke(((leg[0], leg[1] - drop), (leg[0], top + 4)), 2.4))
    screen.pen = color.rgb(150, 150, 156, alpha)
    for side in (-1, 1):
        screen.shape(shape.rectangle(centre_x + side * POT_WIDTH / 2 - 2, top + 14, 4, 12))
    screen.pen = color.rgb(30, 70, 140, alpha)
    screen.shape(shape.rounded_rectangle(centre_x - POT_WIDTH / 2 + 2, top, POT_WIDTH - 4, POT_HEIGHT, 3))
    screen.pen = color.rgb(170, 170, 176, alpha)
    screen.shape(shape.rectangle(centre_x - 7, top + POT_HEIGHT, 14, 4))
    screen.pen = color.rgb(220, 220, 226, alpha)
    screen.shape(shape.rounded_rectangle(centre_x - 5, top + POT_HEIGHT + 4, 10, POT_SHAFT, 2))
    screen.pen = color.rgb(150, 150, 156, alpha)
    for groove in range(3):
        screen.shape(shape.rectangle(centre_x - 5, top + POT_HEIGHT + 8 + groove * 5, 10, 1.5))


def _draw_button(screen, part, drop, alpha):
    _, top_left, bottom_right = part
    centre_x = (top_left[0] + bottom_right[0]) / 2
    centre_y = (top_left[1] + bottom_right[1]) / 2 - drop
    half = BUTTON_SIZE / 2
    screen.pen = color.rgb(196, 196, 202, alpha)
    for x in (top_left[0], bottom_right[0]):
        for y in (top_left[1], bottom_right[1]):
            inner_y = centre_y - half + 4 if y < centre_y + drop else centre_y + half - 4
            screen.shape(_stroke(((x, y - drop), (x, inner_y)), 2.4))
    screen.pen = color.rgb(60, 60, 64, alpha)
    screen.shape(shape.rounded_rectangle(centre_x - half, centre_y - half, BUTTON_SIZE, BUTTON_SIZE, 3))
    screen.pen = color.rgb(40, 40, 44, alpha)
    for dx in (-1, 1):
        for dy in (-1, 1):
            screen.shape(shape.circle(centre_x + dx * (half - 6), centre_y + dy * (half - 6), 3))
    screen.pen = color.rgb(14, 14, 16, alpha)
    screen.shape(shape.circle(centre_x, centre_y, BUTTON_CAP))


def _draw_servo(screen, part, drop, alpha):
    y = SERVO_TOP + (part[1] - 1) * PITCH - drop
    end_x = SERVO_X + PITCH * 2 + 9
    for index, (r, g, b) in enumerate(SERVO_WIRES):
        screen.pen = color.rgb(r, g, b, alpha)
        offset = (index - 1) * 3
        screen.shape(_stroke(((end_x - 2, y + offset), (end_x + 10, y + offset), (330, y + offset + 6)), 2.6))
    screen.pen = color.rgb(36, 36, 40, alpha)
    screen.shape(shape.rounded_rectangle(SERVO_X - 7, y - 6, end_x - SERVO_X + 7, 12, 2))
    for index, (r, g, b) in enumerate(SERVO_WIRES):
        screen.pen = color.rgb(r, g, b, alpha)
        screen.shape(shape.rectangle(SERVO_X + index * PITCH - 3, y + 2, 6, 2))


def _draw_wire(screen, part, progress):
    path = _wire_path(part)
    points = path[:max(2, int(len(path) * progress))]
    rgb = part[3]
    screen.pen = color.rgb(*rgb)
    screen.shape(_stroke(points, 3.5))
    if rgb == BLACK:
        screen.pen = WIRE_SHINE
        screen.shape(_stroke(points, 1.2))


def _timeline(steps):
    timeline = []
    clock = 0
    for _, parts in steps:
        starts = []
        for _ in parts:
            starts.append(clock)
            clock += PLACE_MS + PART_GAP_MS
        timeline.append((clock, starts))
        clock += STEP_HOLD_MS
    return timeline, clock + END_HOLD_MS


def _draw(screen, title_font, body_font, steps, timeline, elapsed):
    current = len(steps) - 1
    for index, (finished, _) in enumerate(timeline):
        if elapsed < finished + STEP_HOLD_MS:
            current = index
            break

    placed = []
    strips = []
    for (_, parts), (_, starts) in zip(steps, timeline):
        for part, start in zip(parts, starts):
            t = (elapsed - start) / PLACE_MS
            if t <= 0:
                continue
            t = _ease(min(1.0, t))
            placed.append((part, t))
            if t >= 1.0:
                for strip in _part_strips(part):
                    if strip not in strips:
                        strips.append(strip)

    screen.pen = INK
    screen.clear()
    _draw_board(screen, strips)
    for part, t in placed:
        alpha = int(255 * min(1.0, t * 2))
        if part[0] == "led":
            _draw_led(screen, part, DROP_HEIGHT * (1 - t), alpha)
        elif part[0] == "pot":
            _draw_potentiometer(screen, part, DROP_HEIGHT * (1 - t), alpha)
        elif part[0] == "rgb":
            _draw_rgb_led(screen, part, DROP_HEIGHT * (1 - t), alpha)
        elif part[0] == "servo":
            _draw_servo(screen, part, DROP_HEIGHT * (1 - t), alpha)
        elif part[0] == "button":
            _draw_button(screen, part, DROP_HEIGHT * (1 - t), alpha)
        else:
            _draw_wire(screen, part, t)

    screen.font = body_font
    screen.pen = DIM
    screen.text(f"{current + 1}/{len(steps)}", 8, 2, 13)
    screen.font = title_font
    screen.pen = PAPER
    screen.text(steps[current][0], rect(34, 2, 280, 30), 13)
    labels.draw(screen, title_font, {"A": labels.Icon("play_circle")}, "A")


def show(steps, title_font, body_font):
    import explorer

    screen = explorer.screen
    previous_font = screen.font
    previous_antialias = screen.antialias
    screen.antialias = image.X2
    timeline, cycle = _timeline(steps)

    started = time.ticks_ms()
    while not explorer.SELECT.pressed:
        elapsed = time.ticks_diff(time.ticks_ms(), started) % cycle
        _draw(screen, title_font, body_font, steps, timeline, elapsed)
        explorer.update()

    while explorer.SELECT.held:
        explorer.poll()
        time.sleep_ms(10)

    screen.font = previous_font
    screen.antialias = previous_antialias
    gc.collect()

import gc
import math
import time
from array import array

from picovector import brush, color, font, image, mat3, rect, shape

ADDRESSES = (0x23, 0x6A, 0x76)
SCAN_MS = 250
CYCLE_MS = 2200
SLIDE = 0.55
CONNECTED_MS = 900
CHECK_MS = 500
FAILURE_LIMIT = 3

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
GOOD = color.rgb(52, 199, 138)
SILK = color.rgb(250, 246, 238)
JST = color.rgb(240, 236, 228)
JST_SHADE = color.rgb(186, 178, 166)
PIN = color.rgb(200, 200, 205)
WIRE_SHINE = color.rgb(120, 118, 112)
BUTTON = color.rgb(38, 38, 40)
SCREEN_GLASS = color.rgb(8, 8, 10)
MOUNTAIN = color.rgb(168, 60, 50)
GOLD = color.rgb(200, 164, 96)
BREADBOARD = color.rgb(26, 26, 28)
BREADBOARD_HOLE = color.rgb(6, 6, 6)
BREADBOARD_RIDGE = color.rgb(44, 44, 46)
STICK_PCB = color.rgb(14, 14, 14)
STICK_EDGE = color.rgb(96, 92, 86)
STICK_PALE_CHIP = color.rgb(190, 186, 180)
ARTWORK = (
    (0.0, color.rgb(214, 96, 50)),
    (0.36, color.rgb(244, 196, 132)),
    (0.5, color.rgb(232, 132, 84)),
    (0.66, color.rgb(176, 62, 52)),
    (0.7, color.rgb(56, 82, 132)),
    (1.0, color.rgb(32, 52, 96)),
)
WIRES = (
    (-4.5, color.rgb(10, 10, 10)),
    (-1.5, color.rgb(235, 60, 50)),
    (1.5, color.rgb(70, 120, 255)),
    (4.5, color.rgb(255, 204, 51)),
)

BOARD_EDGE = 206
SOCKET_LEFT = 210
SOCKET_WIDTH = 20
SOCKET_HEIGHT = 30
UPPER_SOCKET_Y = 93
PLUG_Y = 150
PLUG_BACK = 7
PLUG_BACK_HEIGHT = 26
PLUG_NOSE = 18
PLUG_NOSE_HEIGHT = 19
PLUG_IN_X = SOCKET_LEFT - PLUG_BACK
PLUG_OUT_X = 168
STICK_RIGHT = 146
STICK_LEFT = STICK_RIGHT - 229
STICK_Y = 190
STICK_HEIGHT = 34
WIRE_TUCK = 2
STROKE_NUDGE = -1

_board = []


def present(bus):
    for address in ADDRESSES:
        try:
            bus.readfrom(address, 1)
        except OSError:
            return False
    return True


def connected(bus):
    try:
        found = bus.scan()
    except OSError:
        return False
    return all(address in found for address in ADDRESSES)


def _ease(t):
    return 1 - (1 - t) ** 3


def _cable_path(plug_x):
    x0, y0 = STICK_RIGHT + PLUG_BACK - WIRE_TUCK, STICK_Y + STROKE_NUDGE
    x3, y3 = plug_x + WIRE_TUCK, PLUG_Y + STROKE_NUDGE
    reach = max(12, (x3 - x0) * 0.5)
    c1x, c2x = x0 + reach, x3 - reach
    path = []
    for step in range(25):
        t = step / 24
        u = 1 - t
        path.append((
            u * u * u * x0 + 3 * u * u * t * c1x + 3 * u * t * t * c2x + t * t * t * x3,
            u * u * u * y0 + 3 * u * u * t * y0 + 3 * u * t * t * y3 + t * t * t * y3,
        ))
    return path


def _strand(path, offset, width):
    points = array("f")
    last = len(path) - 1
    for index, (x, y) in enumerate(path):
        ax, ay = path[max(0, index - 1)]
        bx, by = path[min(last, index + 1)]
        length = math.sqrt((bx - ax) ** 2 + (by - ay) ** 2) or 1
        points.append(x + (ay - by) / length * offset)
        points.append(y + (bx - ax) / length * offset)
    return shape.custom(points).stroke(width, shape.PATH_OPEN | shape.JOIN_ROUND | shape.CAP_BUTT)


def _jst_shapes(left, y, opening_left=True):
    top = y - SOCKET_HEIGHT / 2
    back = left + SOCKET_WIDTH - 3 if opening_left else left
    pins = left + SOCKET_WIDTH if opening_left else left - 6
    shapes = [
        (shape.rectangle(left, top, SOCKET_WIDTH, SOCKET_HEIGHT), JST),
        (shape.rectangle(left, top, SOCKET_WIDTH, 2), JST_SHADE),
        (shape.rectangle(back, top + 3, 3, SOCKET_HEIGHT - 6), JST_SHADE),
    ]
    for pin in range(4):
        shapes.append((shape.rectangle(pins, y - 9 + pin * 6, 6, 2), PIN))
    return shapes


def _socket_shapes(y):
    return _jst_shapes(SOCKET_LEFT, y)


def _plug_shapes(back_left, y, nose_right=True):
    nose_left = back_left + PLUG_BACK if nose_right else back_left - PLUG_NOSE
    shade = back_left + PLUG_BACK - 2 if nose_right else back_left
    return (
        (shape.rectangle(back_left, y - PLUG_BACK_HEIGHT / 2, PLUG_BACK, PLUG_BACK_HEIGHT), JST),
        (shape.rectangle(nose_left, y - PLUG_NOSE_HEIGHT / 2, PLUG_NOSE, PLUG_NOSE_HEIGHT), JST),
        (shape.rectangle(shade, y - PLUG_BACK_HEIGHT / 2, 2, PLUG_BACK_HEIGHT), JST_SHADE),
    )


def _draw_shapes(screen, shapes):
    for item, pen in shapes:
        screen.pen = pen
        screen.shape(item)


def _build_board():
    artwork = brush.gradient(brush.LINEAR, 0, 0, 0, 240, ARTWORK)
    mountains = array("f", (BOARD_EDGE, 162, BOARD_EDGE + 10, 136, BOARD_EDGE + 22, 146, BOARD_EDGE + 38, 118, BOARD_EDGE + 54, 134, BOARD_EDGE + 68, 124, BOARD_EDGE + 90, 142, 320, 130, 320, 170, BOARD_EDGE, 170))
    _board.extend((
        (shape.rectangle(BOARD_EDGE, 0, 320 - BOARD_EDGE, 240), artwork),
        (shape.custom(mountains), MOUNTAIN),
        (shape.rounded_rectangle(BOARD_EDGE + 2, 8, 27, 27, 6), BUTTON),
        (shape.rectangle(BOARD_EDGE + 12, 4, 7, 3), SILK),
        (shape.rectangle(BOARD_EDGE + 12, 36, 7, 3), SILK),
        (shape.rectangle(BOARD_EDGE + 45, 0, 320 - BOARD_EDGE - 45, 66), SILK),
        (shape.rounded_rectangle(BOARD_EDGE + 47, -4, 320 - BOARD_EDGE - 47, 68, 2), SCREEN_GLASS),
        (shape.rounded_rectangle(BOARD_EDGE, 172, 28, 28, 14), GOLD),
        (shape.rectangle(BOARD_EDGE, 172, 14, 28), GOLD),
        (shape.circle(BOARD_EDGE + 14, 186, 8), INK),
        (shape.rounded_rectangle(BOARD_EDGE + 58, 122, 320 - BOARD_EDGE - 58, 130, 3), BREADBOARD),
        (shape.rectangle(BOARD_EDGE + 58, 193, 320 - BOARD_EDGE - 58, 16), BREADBOARD_RIDGE),
    ))
    for x, y in ((BOARD_EDGE + 40, 14), (BOARD_EDGE + 30, 48), (BOARD_EDGE + 62, 78), (BOARD_EDGE + 96, 86), (BOARD_EDGE + 20, 70)):
        _board.append((shape.circle(x, y, 1), SILK))
    for row in range(13):
        y = 128 + row * 9
        if 189 < y < 210:
            continue
        for column in range(6):
            _board.append((shape.rectangle(BOARD_EDGE + 64 + column * 9, y, 4, 4), BREADBOARD_HOLE))
    _board.extend(_socket_shapes(UPPER_SOCKET_Y))


def _draw_board(screen, title_font):
    if not _board:
        _build_board()
    for item, pen in _board:
        screen.pen = pen
        screen.shape(item)
    screen.font = title_font
    screen.pen = SILK
    screen.text("C", BOARD_EDGE + 10, 44, 14)
    screen.text("SCREEN", BOARD_EDGE + 52, 69, 8)
    screen.text("QW/ST", BOARD_EDGE + 5, 108, 8)
    screen.text("I2C", BOARD_EDGE + 5, 116, 8)
    screen.text("GND", BOARD_EDGE + 2, 200, 8)
    anchor_x, anchor_y = BOARD_EDGE + 40, 236
    screen.text("CONNECTIONS", anchor_x, anchor_y, 8, transform=mat3().translate(anchor_x, anchor_y).rotate(-90).translate(-anchor_x, -anchor_y))


def _draw_stick(screen):
    width = STICK_RIGHT - STICK_LEFT
    top = STICK_Y - STICK_HEIGHT / 2
    screen.pen = STICK_EDGE
    screen.shape(shape.rounded_rectangle(STICK_LEFT - 1.5, top - 1.5, width + 3, STICK_HEIGHT + 3, 6))
    screen.pen = STICK_PCB
    screen.shape(shape.rounded_rectangle(STICK_LEFT, top, width, STICK_HEIGHT, 5))
    for x in (STICK_RIGHT - 182, STICK_RIGHT - 46):
        screen.pen = STICK_EDGE
        screen.shape(shape.circle(x, STICK_Y, 7.5))
        screen.pen = INK
        screen.shape(shape.circle(x, STICK_Y, 6))
    screen.pen = STICK_PALE_CHIP
    screen.shape(shape.rectangle(STICK_RIGHT - 151, STICK_Y - 6, 11, 11))
    screen.shape(shape.rectangle(STICK_RIGHT - 114, STICK_Y - 8, 16, 16))
    screen.pen = STICK_PCB
    screen.shape(shape.rectangle(STICK_RIGHT - 112.5, STICK_Y - 6.5, 13, 13))
    screen.pen = STICK_EDGE
    screen.shape(shape.rectangle(STICK_RIGHT - 78, STICK_Y - 5, 16, 9))
    _draw_shapes(screen, _jst_shapes(STICK_LEFT, STICK_Y))


def _draw(screen, title_font, plug_x, done):
    screen.pen = INK
    screen.clear()

    _draw_board(screen, title_font)

    screen.font = title_font
    screen.pen = GOOD if done else PAPER
    screen.text("Connected!" if done else "Plug in the sensor stick", rect(10, 10, 186, 60), 22)
    if not done:
        screen.pen = DIM
        screen.text("Use the Qw/ST connector on the left edge of Explorer", rect(10, 70, 186, 60), 14)

    _draw_stick(screen)
    path = _cable_path(plug_x)
    for offset, pen in WIRES:
        screen.pen = pen
        screen.shape(_strand(path, offset, 2.6))
    screen.pen = WIRE_SHINE
    screen.shape(_strand(path, WIRES[0][0], 1.2))
    _draw_shapes(screen, _plug_shapes(STICK_RIGHT, STICK_Y, nose_right=False))
    _draw_shapes(screen, _jst_shapes(STICK_RIGHT - SOCKET_WIDTH, STICK_Y, opening_left=False))
    _draw_shapes(screen, _plug_shapes(plug_x, PLUG_Y))
    _draw_shapes(screen, _socket_shapes(PLUG_Y))


def wait(explorer, title_font=None):
    bus = explorer.i2c()
    if connected(bus):
        return bus

    screen = explorer.screen
    previous_font = screen.font
    previous_antialias = screen.antialias
    screen.antialias = image.X2
    if title_font is None:
        title_font = font.load("/rom/fonts/manrope-800.af")

    started = time.ticks_ms()
    last_scan = started
    while True:
        now = time.ticks_ms()
        if time.ticks_diff(now, last_scan) >= SCAN_MS:
            last_scan = now
            if connected(bus):
                break
        cycle = (time.ticks_diff(now, started) % CYCLE_MS) / CYCLE_MS
        slide = _ease(min(1.0, cycle / SLIDE))
        _draw(screen, title_font, PLUG_OUT_X + (PLUG_IN_X - PLUG_OUT_X) * slide, False)
        explorer.update()

    explorer.beep(880, 80)
    _draw(screen, title_font, PLUG_IN_X, True)
    explorer.update()
    finished = time.ticks_add(time.ticks_ms(), CONNECTED_MS)
    while time.ticks_diff(finished, time.ticks_ms()) > 0:
        explorer.poll()
        time.sleep_ms(10)

    screen.font = previous_font
    screen.antialias = previous_antialias
    title_font = None
    _board.clear()
    gc.collect()
    return bus


class Sensor:
    def __init__(self, explorer, factory, title_font, on_disconnect):
        self._explorer = explorer
        self._factory = factory
        self._title_font = title_font
        self._on_disconnect = on_disconnect
        self._last = {}
        self._connect()

    def _connect(self):
        while True:
            self._bus = wait(self._explorer, self._title_font)
            try:
                self._device = self._factory(self._bus)
                break
            except (OSError, RuntimeError):
                pass
        self._failures = 0
        self._checked = time.ticks_ms()

    def _call(self, name, args, kwargs):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._checked) >= CHECK_MS:
            self._checked = now
            if not present(self._bus):
                self._failures = FAILURE_LIMIT
        if self._failures < FAILURE_LIMIT:
            try:
                result = getattr(self._device, name)(*args, **kwargs)
            except (OSError, RuntimeError):
                self._failures += 1
            else:
                self._failures = 0
                self._last[name] = result
                return result
        if self._failures < FAILURE_LIMIT and name in self._last:
            return self._last[name]
        if self._on_disconnect is not None:
            self._on_disconnect()
        self._connect()
        return self._call(name, args, kwargs)

    def __getattr__(self, name):
        attribute = getattr(self._device, name)
        if not callable(attribute):
            return attribute

        def call(*args, **kwargs):
            return self._call(name, args, kwargs)

        return call

from picovector import color, font, shape

ROWS = (45, 119, 191)
POSITIONS = {
    "A": (ROWS[0], False),
    "B": (ROWS[1], False),
    "C": (ROWS[2], False),
    "X": (ROWS[0], True),
    "Y": (ROWS[1], True),
    "Z": (ROWS[2], True),
}
SCREEN_WIDTH = 320
RADIUS = 13
EDGE_PADDING = 9
TEXT_SIZE = 15
CAP_CENTRE = 0.64
CHROME = color.rgb(239, 235, 227)
HIGHLIGHT = color.rgb(255, 204, 51)
INK = color.rgb(31, 29, 27)
ICON_PILL_WIDTH = 28
ICON_SIZE = 20

_icon_font = None
_icon_codes = {}


class Icon:
    def __init__(self, name):
        self.name = name


def _load_icons():
    global _icon_font
    if _icon_font is None:
        _icon_font = font.load("/rom/fonts/icons.af")
        with open("/rom/fonts/icons.txt") as names:
            for line in names:
                name, codepoint = line.split()
                _icon_codes[name] = chr(int(codepoint, 16))
    return _icon_font


def pill(screen, letter, label, highlighted=False):
    y, mirrored = POSITIONS[letter]
    label_width = screen.measure_text(label, font_size=TEXT_SIZE)[0]
    width = RADIUS + EDGE_PADDING + label_width + RADIUS
    if mirrored:
        left = SCREEN_WIDTH + RADIUS - width
        label_x = SCREEN_WIDTH - EDGE_PADDING - label_width
    else:
        left = -RADIUS
        label_x = EDGE_PADDING

    screen.pen = HIGHLIGHT if highlighted else CHROME
    screen.shape(shape.rounded_rectangle(left, y - RADIUS, width, RADIUS * 2, RADIUS))
    screen.pen = INK
    screen.text(label, label_x, y - TEXT_SIZE * CAP_CENTRE, TEXT_SIZE)


def icon_pill(screen, letter, name, highlighted=False):
    y, mirrored = POSITIONS[letter]
    if mirrored:
        left = SCREEN_WIDTH - ICON_PILL_WIDTH
        centre_x = left + RADIUS
    else:
        left = -RADIUS
        centre_x = ICON_PILL_WIDTH - RADIUS
    screen.pen = HIGHLIGHT if highlighted else CHROME
    screen.shape(shape.rounded_rectangle(left, y - RADIUS, ICON_PILL_WIDTH + RADIUS, RADIUS * 2, RADIUS))
    previous_font = screen.font
    screen.font = _load_icons()
    screen.pen = INK
    screen.text(_icon_codes.get(name, ""), centre_x, y - ICON_SIZE / 2, ICON_SIZE / 2)
    screen.font = previous_font


def draw(screen, title_font, actions, highlight=None):
    previous_font = screen.font
    screen.font = title_font
    for letter, label in actions.items():
        if isinstance(label, Icon):
            icon_pill(screen, letter, label.name, letter == highlight)
        else:
            pill(screen, letter, label, letter == highlight)
    screen.font = previous_font

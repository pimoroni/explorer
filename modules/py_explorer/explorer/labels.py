from picovector import color, shape

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


def draw(screen, title_font, actions, highlight=None):
    previous_font = screen.font
    screen.font = title_font
    for letter, label in actions.items():
        pill(screen, letter, label, letter == highlight)
    screen.font = previous_font

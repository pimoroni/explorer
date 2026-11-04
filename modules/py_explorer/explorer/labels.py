from picovector import color, shape

LEFT_X = 16
RIGHT_X = 304
ROWS = (45, 119, 191)
POSITIONS = {
    "A": (LEFT_X, ROWS[0], False),
    "B": (LEFT_X, ROWS[1], False),
    "C": (LEFT_X, ROWS[2], False),
    "X": (RIGHT_X, ROWS[0], True),
    "Y": (RIGHT_X, ROWS[1], True),
    "Z": (RIGHT_X, ROWS[2], True),
}
RADIUS = 13
TEXT_SIZE = 15
CAP_CENTRE = 0.64
CHROME = color.rgb(239, 235, 227)
INK = color.rgb(31, 29, 27)
DIVIDER = color.rgb(31, 29, 27, 70)


def _text_at_caps(screen, text, x, y):
    screen.text(text, x, y - TEXT_SIZE * CAP_CENTRE, TEXT_SIZE)


def pill(screen, letter, label):
    x, y, mirrored = POSITIONS[letter]
    letter_width = screen.measure_text(letter, font_size=TEXT_SIZE)[0]
    label_width = screen.measure_text(label, font_size=TEXT_SIZE)[0] if label else 0
    width = RADIUS * 2 + (label_width + 14 if label else 0)
    if mirrored:
        left = x + RADIUS - width
        divider = x - RADIUS + 3
        label_x = divider - 7 - label_width
    else:
        left = x - RADIUS
        divider = x + RADIUS - 3
        label_x = divider + 7

    screen.pen = CHROME
    screen.shape(shape.rounded_rectangle(left, y - RADIUS, width, RADIUS * 2, RADIUS))
    screen.pen = INK
    _text_at_caps(screen, letter, x - letter_width / 2, y)
    if label:
        screen.pen = DIVIDER
        screen.shape(shape.line(divider, y - 6, divider, y + 6, 1.5))
        screen.pen = INK
        _text_at_caps(screen, label, label_x, y)


def draw(screen, title_font, actions):
    previous_font = screen.font
    screen.font = title_font
    for letter, label in actions.items():
        pill(screen, letter, label)
    screen.font = previous_font

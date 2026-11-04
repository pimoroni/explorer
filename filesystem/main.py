import gc
import os
import time
from array import array

import explorer
from explorer import button_a, button_b, button_c, button_x, button_z, screen
from picovector import color, font, image, rect, shape, tween

APPS_DIR = "/apps"

screen.antialias = image.X4

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")
ICON_FONT = font.load("/rom/fonts/icons.af")

BACKGROUND = color.rgb(0, 0, 0)
CHROME = color.rgb(239, 235, 227)
INK = color.rgb(31, 29, 27)
ACCENT = color.rgb(255, 90, 31)
FAINT = color.rgb(58, 56, 53)
DIM = color.rgb(125, 120, 112)
CARD_COLOURS = (
    (255, 122, 61),
    (255, 204, 51),
    (92, 150, 255),
    (52, 199, 138),
    (214, 211, 204),
    (255, 143, 177),
)

ROW_CENTRES = (45, 119, 191)
ROW_HEIGHT = 62
CARD_LEFT = 16
CARD_RIGHT = 290
DETAIL_RIGHT = 316
BADGE_RADIUS = 11
DETAIL_TOP = 6
DETAIL_BOTTOM = 234
ROW_ICON_SIZE = 40
DETAIL_ICON_SIZE = 52
ROW_BUTTONS = (button_a, button_b, button_c)
TRANSITION_MS = 280
PILL_EASE = tween(0.0, 1.0, easing=tween.BACK_OUT)
MOVE_EASE = tween(0.0, 1.0, easing=tween.CUBIC_OUT)
PILL_DELAY = 0.25
CHROME_X = 309
CHEVRON_RADIUS = 9
DETAIL_TEXT_LEFT = 48
DETAIL_TEXT_WIDTH = DETAIL_RIGHT - DETAIL_TEXT_LEFT - 10
ACTION_RADIUS = 13
ACTION_ICON_X = 18
ACTION_ICON_SIZE = 20
ACTION_WIDTH = ACTION_ICON_X + 9 + ACTION_RADIUS
NEEDS_WIDTH = 216
NEEDS_LINE = 20
DETAIL_TITLE_Y = 30
DETAIL_ICON_X = DETAIL_RIGHT - DETAIL_ICON_SIZE / 2 - 16
DETAIL_ICON_Y = DETAIL_TOP + DETAIL_ICON_SIZE / 2 + 12
DETAIL_DESCRIPTION_Y = 72

FALLBACK_ICON = "apps"
CAP_CENTRE = 0.64
STROKE = shape.PATH_OPEN | shape.JOIN_ROUND | shape.CAP_ROUND


def load_icons():
    icons = {}
    try:
        with open("/rom/fonts/icons.txt") as names:
            for line in names:
                name, codepoint = line.split()
                icons[name] = chr(int(codepoint, 16))
    except OSError:
        pass
    return icons


ICONS = load_icons()


class App:
    def __init__(self, path):
        self.path = path
        name = path.rsplit("/", 1)[-1][:-3]
        self.title = " ".join(word[:1].upper() + word[1:] for word in name.split("_"))
        self.description = ""
        self.needs = []
        self.icon = ICONS.get(FALLBACK_ICON, "")
        self._read_header()

    def _read_header(self):
        try:
            with open(self.path) as source:
                head = source.read(1024)
        except OSError:
            return
        if not head.startswith('"""'):
            return
        end = head.find('"""', 3)
        lines = [line.strip() for line in head[3:end if end > 0 else None].split("\n")]
        if lines and lines[0]:
            self.title = lines[0]
        description = []
        in_needs = False
        for line in lines[1:]:
            if line.lower().startswith("you will need"):
                in_needs = True
            elif line.startswith("Icon:"):
                self.icon = ICONS.get(line[5:].strip(), self.icon)
                in_needs = False
            elif in_needs and line.startswith("-"):
                self.needs.append(line[1:].strip())
            elif line and not in_needs:
                description.append(line)
        self.description = " ".join(description)


def find_apps():
    try:
        names = sorted(name for name in os.listdir(APPS_DIR) if name.endswith(".py"))
    except OSError:
        names = []
    return [App(f"{APPS_DIR}/{name}") for name in names]


def card_colour(index, alpha=255):
    r, g, b = CARD_COLOURS[index % len(CARD_COLOURS)]
    return color.rgb(r, g, b, alpha)


def draw_icon(app, x, y, size):
    screen.font = ICON_FONT
    screen.pen = INK
    screen.text(app.icon, x, y - size / 2, size / 2)


def fit_text(text, max_width, size, smallest):
    while size > smallest and screen.measure_text(text, font_size=size)[0] > max_width:
        size -= 1
    return size


def text_at_caps(text, x, y, size, centred=False):
    if centred:
        x -= screen.measure_text(text, font_size=size)[0] / 2
    screen.text(text, x, y - size * CAP_CENTRE, size)


def draw_badge(label, y, enabled=True, x=CARD_LEFT):
    screen.pen = CHROME if enabled else FAINT
    screen.shape(shape.circle(x, y, BADGE_RADIUS))
    screen.font = TITLE_FONT
    screen.pen = INK if enabled else DIM
    text_at_caps(label, x, y, 13, centred=True)


def draw_chevron(y, up, enabled, x):
    screen.pen = CHROME if enabled else FAINT
    screen.shape(shape.circle(x, y, CHEVRON_RADIUS))
    screen.pen = INK if enabled else DIM
    tip = y - 3 if up else y + 3
    base = y + 2 if up else y - 2
    screen.shape(shape.custom(array("f", (x - 4, base, x, tip, x + 4, base))).stroke(2, STROKE))


def draw_scrollbar(page, pages, x):
    top = 64
    bottom = 172
    screen.pen = FAINT
    screen.shape(shape.line(x, top, x, bottom, 2))
    if pages <= 1:
        return
    length = max(14, (bottom - top) / pages)
    start = top + (bottom - top - length) * page / (pages - 1)
    screen.pen = ACCENT
    screen.shape(shape.line(x, start, x, start + length, 4))


def draw_chrome(page, pages, x=CHROME_X):
    draw_chevron(ROW_CENTRES[0], True, page > 0, x)
    draw_chevron(ROW_CENTRES[2], False, page < pages - 1, x)
    draw_scrollbar(page, pages, x)


def row_layout(app, centre):
    icon_x = CARD_RIGHT - ROW_ICON_SIZE / 2 - 14
    screen.font = TITLE_FONT
    size = fit_text(app.title, icon_x - ROW_ICON_SIZE / 2 - CARD_LEFT - BADGE_RADIUS - 18, 26, 16)
    return icon_x, centre, ROW_ICON_SIZE, CARD_LEFT + BADGE_RADIUS + 10, centre, size


def detail_layout(app):
    screen.font = TITLE_FONT
    size = fit_text(app.title, DETAIL_ICON_X - DETAIL_ICON_SIZE / 2 - DETAIL_TEXT_LEFT - 8, 26, 18)
    return DETAIL_ICON_X, DETAIL_ICON_Y, DETAIL_ICON_SIZE, DETAIL_TEXT_LEFT, DETAIL_TITLE_Y, size


def draw_row(app, index, centre):
    top = centre - ROW_HEIGHT // 2
    screen.pen = card_colour(index)
    screen.shape(shape.rectangle(CARD_LEFT, top, CARD_RIGHT - CARD_LEFT, ROW_HEIGHT))
    icon_x, icon_y, icon_size, title_x, title_y, size = row_layout(app, centre)
    draw_icon(app, icon_x, icon_y, icon_size)
    screen.font = TITLE_FONT
    screen.pen = INK
    text_at_caps(app.title, title_x, title_y, size)


def page_count(apps):
    return (len(apps) + 2) // 3


def slot_enabled(apps, page, slot):
    return page * 3 + slot < len(apps)


def draw_list(apps, page):
    screen.pen = BACKGROUND
    screen.clear()
    for slot in range(3):
        if slot_enabled(apps, page, slot):
            draw_row(apps[page * 3 + slot], page * 3 + slot, ROW_CENTRES[slot])
        draw_badge(ROW_BUTTONS[slot].name, ROW_CENTRES[slot], slot_enabled(apps, page, slot))
    draw_chrome(page, page_count(apps))


def draw_action(letter, icon, x, y, t, mirrored=False, from_chevron=False, chevron_enabled=True):
    if from_chevron and t <= 0:
        draw_chevron(y, False, chevron_enabled, x)
        return
    start_radius = CHEVRON_RADIUS if from_chevron else BADGE_RADIUS
    grow = min(1.0, max(0.0, t))
    radius = start_radius + (ACTION_RADIUS - start_radius) * grow
    if mirrored:
        end_left, end_right = explorer.WIDTH - ACTION_WIDTH, explorer.WIDTH + ACTION_RADIUS
        end_x = explorer.WIDTH - ACTION_ICON_X
    else:
        end_left, end_right = -ACTION_RADIUS, ACTION_WIDTH
        end_x = ACTION_ICON_X
    left = x - start_radius + (end_left - x + start_radius) * t
    right = x + start_radius + (end_right - x - start_radius) * t
    centre_x = x + (end_x - x) * t

    screen.pen = CHROME
    screen.shape(shape.rounded_rectangle(left, y - radius, right - left, radius * 2, radius))
    fade_out = max(0.0, 1 - grow * 2)
    fade_in = min(1.0, max(0.0, grow * 2 - 1))
    if fade_out > 0:
        screen.font = TITLE_FONT
        screen.pen = color.rgb(31, 29, 27, int(255 * fade_out))
        if from_chevron:
            screen.shape(shape.custom(array("f", (centre_x - 4, y - 2, centre_x, y + 3, centre_x + 4, y - 2))).stroke(2, STROKE))
        else:
            text_at_caps(letter, centre_x, y, 13, centred=True)
    if fade_in > 0:
        screen.font = ICON_FONT
        screen.pen = color.rgb(31, 29, 27, int(255 * fade_in))
        screen.text(ICONS.get(icon, ""), centre_x, y - ACTION_ICON_SIZE / 2, ACTION_ICON_SIZE / 2)


def wrap_text(text, width, size):
    lines = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}" if line else word
        if line and screen.measure_text(candidate, font_size=size)[0] > width:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def draw_detail_text(app, alpha):
    if alpha <= 0:
        return
    ink = color.rgb(31, 29, 27, int(255 * alpha))
    screen.font = BODY_FONT
    screen.pen = ink
    screen.text(app.description, rect(DETAIL_TEXT_LEFT, DETAIL_DESCRIPTION_Y, DETAIL_TEXT_WIDTH, 48), 16)
    if app.needs:
        screen.font = TITLE_FONT
        screen.text("You will need", DETAIL_TEXT_LEFT, 128, 16)
        screen.font = BODY_FONT
        y = 152
        for item in app.needs:
            lines = wrap_text(item, NEEDS_WIDTH, 16)
            if y + len(lines) * NEEDS_LINE > DETAIL_BOTTOM:
                break
            screen.shape(shape.circle(DETAIL_TEXT_LEFT + 4, y + 9, 3))
            for line in lines:
                screen.text(line, DETAIL_TEXT_LEFT + 14, y, 16)
                y += NEEDS_LINE


def draw_transition(apps, page, slot, progress):
    index = page * 3 + slot
    move = MOVE_EASE.at(progress)
    pill = PILL_EASE.at(max(0.0, (progress - PILL_DELAY) / (1 - PILL_DELAY)))
    slide = move

    screen.pen = BACKGROUND
    screen.clear()
    if progress < 1.0:
        for other in range(3):
            if slot_enabled(apps, page, other):
                draw_row(apps[page * 3 + other], page * 3 + other, ROW_CENTRES[other])

    centre = ROW_CENTRES[slot]
    top = (centre - ROW_HEIGHT // 2) * (1 - move) + DETAIL_TOP * move
    bottom = (centre + ROW_HEIGHT // 2) * (1 - move) + DETAIL_BOTTOM * move
    screen.pen = card_colour(index)
    right = CARD_RIGHT + (DETAIL_RIGHT - CARD_RIGHT) * slide
    screen.shape(shape.rectangle(CARD_LEFT, top, right - CARD_LEFT, bottom - top))

    app = apps[index]
    start = row_layout(app, centre)
    end = detail_layout(app)
    icon_x, icon_y, icon_size, title_x, title_y, size = (a + (b - a) * move for a, b in zip(start, end))
    draw_icon(app, icon_x, icon_y, icon_size)
    screen.font = TITLE_FONT
    screen.pen = INK
    text_at_caps(app.title, title_x, title_y, size)
    draw_detail_text(app, min(1.0, max(0.0, (progress - 0.6) / 0.4)))

    if slide < 1.0:
        badge_x = CARD_LEFT - (BADGE_RADIUS * 2 + 6) * slide
        for other in range(3):
            if other != slot:
                draw_badge(ROW_BUTTONS[other].name, ROW_CENTRES[other], slot_enabled(apps, page, other), badge_x)
        chrome_x = CHROME_X + (DETAIL_RIGHT - CARD_RIGHT) * slide
        draw_chevron(ROW_CENTRES[0], True, page > 0, chrome_x)
        draw_scrollbar(page, page_count(apps), chrome_x)
    draw_action(ROW_BUTTONS[slot].name, "arrow_back", CARD_LEFT, centre, pill)
    draw_action(button_z.name, "play_arrow", CHROME_X, ROW_CENTRES[2], pill, mirrored=True, from_chevron=True, chevron_enabled=page < page_count(apps) - 1)


def animate(apps, page, slot, forward):
    started = time.ticks_ms()
    while True:
        progress = min(1.0, time.ticks_diff(time.ticks_ms(), started) / TRANSITION_MS)
        draw_transition(apps, page, slot, progress if forward else 1.0 - progress)
        explorer.update()
        if progress >= 1.0:
            return


def idle():
    explorer.poll()
    time.sleep_ms(10)


def menu():
    apps = find_apps()
    if not apps:
        explorer.show_error("No apps", f"Copy some .py files into {APPS_DIR}")
        return None

    pages = page_count(apps)
    page = 0
    draw_list(apps, page)
    explorer.update()
    while explorer.held():
        idle()

    while True:
        chosen = None
        if button_x.pressed and page > 0:
            page -= 1
            explorer.beep(660, 50)
        elif button_z.pressed and page < pages - 1:
            page += 1
            explorer.beep(590, 50)
        else:
            for slot, button in enumerate(ROW_BUTTONS):
                if button.pressed and page * 3 + slot < len(apps):
                    chosen = slot
            if chosen is None:
                idle()
                continue

        if chosen is None:
            draw_list(apps, page)
            explorer.update()
            continue

        app = apps[page * 3 + chosen]
        explorer.beep(740, 50)
        animate(apps, page, chosen, forward=True)
        while True:
            if button_z.pressed:
                explorer.beep(880, 80)
                return app.path
            if ROW_BUTTONS[chosen].pressed:
                explorer.beep(494, 50)
                break
            idle()

        animate(apps, page, chosen, forward=False)
        draw_list(apps, page)
        explorer.update()


app_path = menu()
if app_path is not None:
    while explorer.held():
        explorer.poll()
    screen.font = font.sins
    del TITLE_FONT, BODY_FONT, ICON_FONT, ICONS
    gc.collect()
    explorer.launch(app_path)

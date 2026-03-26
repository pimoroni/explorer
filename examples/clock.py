import gc
import time
import pngdec
from explorer import display, button_a, BLACK
from picovector import ANTIALIAS_X16, PicoVector, Polygon, Transform

DIGITAL = True

button = button_a  # Button Aaaaaaa

png = pngdec.PNG(display)

vector = PicoVector(display)
vector.set_antialiasing(ANTIALIAS_X16)

# Custom colours
YELLOW = display.create_pen(200, 150, 50)
GREY = display.create_pen(200, 200, 200)
WHITE = display.create_pen(215, 215, 255)
BLUE = display.create_pen(23, 52, 93)

WIDTH, HEIGHT = display.get_bounds()

# Clear all layers first
display.set_layer(0)
display.set_pen(BLACK)
display.clear()
display.set_layer(1)
display.set_pen(BLACK)
display.clear()

t = Transform()

days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

hub = Polygon()
hub.circle(int(WIDTH / 2), int(HEIGHT / 2), 5)

face = Polygon()
face.circle(int(WIDTH / 2), int(HEIGHT / 2), int(HEIGHT / 2))

tick_mark = Polygon()
tick_mark.rectangle(int(WIDTH / 2) - 3, 10, 4, int(HEIGHT / 48))

hour_mark = Polygon()
hour_mark.rectangle(int(WIDTH / 2) - 4, 10, 8, int(HEIGHT / 12))

second_hand_length = int(HEIGHT / 2) - int(HEIGHT / 8)
second_hand = Polygon()
second_hand.path((-2, -second_hand_length), (-2, int(HEIGHT / 8)), (2, int(HEIGHT / 8)), (2, -second_hand_length))

minute_hand_length = int(HEIGHT / 2) - int(HEIGHT / 24)
minute_hand = Polygon()
minute_hand.path((-5, -minute_hand_length), (-10, int(HEIGHT / 16)), (10, int(HEIGHT / 16)), (5, -minute_hand_length))

hour_hand_length = int(HEIGHT / 2) - int(HEIGHT / 8)
hour_hand = Polygon()
hour_hand.path((-5, -hour_hand_length), (-10, int(HEIGHT / 16)), (10, int(HEIGHT / 16)), (5, -hour_hand_length))

vector.set_font("clock.af", 54)
vector.set_font_letter_spacing(100)
vector.set_font_word_spacing(100)
vector.set_transform(t)


def background_init():
    display.set_layer(0)
    png.open_file("backgroundforscreen.png")
    png.decode()


def digital_init():
    background_init()

    # Bake the "unlit" digits into layer 0
    display.set_pen(BLUE)
    vector.set_font_size(53)
    vector.text("88:88:88", 17, 100)
    vector.set_font_size(28)
    vector.text("888888888888888", 17, 140)

    display.set_layer(1)
    display.set_pen(BLACK)
    display.clear()


def analog_init():
    background_init()

    vector.set_transform(t)

    t.reset()
    display.set_pen(BLUE)
    for a in range(60):
        if a % 5 == 0:
            vector.draw(hour_mark)
        else:
            vector.draw(tick_mark)
        t.rotate(360 / 60.0, (WIDTH / 2, HEIGHT / 2))

    display.set_layer(1)
    display.set_pen(BLACK)
    display.clear()


digital_init()


while True:
    if DIGITAL:
        t.reset()
        display.set_pen(BLACK)
        # Erase only the region we're redrawing!
        display.rectangle(0, 45, 320, 96)

        year, month, day, hour, minute, second, wd, _ = time.localtime()

        # time.ticks_ms() is *not* in sync with time.localtime's "second"
        second = int(time.ticks_ms() / 1000) % 60

        display.set_pen(WHITE)
        c = " " if int(time.ticks_ms() / 500) % 2 else ":"
        vector.set_font_size(53)
        vector.text(f"{hour:02}{c}{minute:02}{c}{second:02}", 17, 100)
        vector.set_font_size(28)
        text = f"{days[wd]} {months[month-1]} {day:02}"
        text = f"{text:30}"
        offset = int(time.ticks_ms() / 200) % len(text)
        vector.text((text[offset:] + text[:offset])[:15], 17, 140)

        display.update()
        gc.collect()
        if not button.value():
            DIGITAL = False
            analog_init()

    else:
        t.reset()
        vector.set_transform(t)
        year, month, day, hour, minute, second, _, _ = time.localtime()
        second_frac = (time.ticks_ms() / 1000) % 60

        display.set_pen(0)
        display.rectangle(40, 0, 240, 240)

        display.set_pen(WHITE)

        t.reset()
        angle_minute = minute * 6
        angle_minute += second / 10.0
        t.translate(WIDTH / 2, HEIGHT / 2)
        t.rotate(angle_minute, (0, 0))
        vector.draw(minute_hand)

        t.reset()
        angle_hour = (hour % 12) * 30
        angle_hour += minute / 2
        t.translate(WIDTH / 2, HEIGHT / 2)
        t.rotate(angle_hour, (0, 0))
        vector.draw(hour_hand)

        display.set_pen(YELLOW)

        t.reset()
        t.translate(WIDTH / 2, HEIGHT / 2)
        t.rotate(second_frac * 6, (0, 0))
        vector.draw(second_hand)

        vector.set_transform(None)
        vector.draw(hub)

        display.update()
        gc.collect()
        if not button.value():
            DIGITAL = True
            digital_init()

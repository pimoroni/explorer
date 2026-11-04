# Explorer boot menu/loader.

import gc
import time
from os import listdir
import pngdec
from explorer import display, button_z, button_x, button_y, BLACK, WHITE

last_button_press = time.ticks_ms()


def hsv_to_rgb(h: float, s: float, v: float) -> tuple[float, float, float]:
    if s == 0.0:
        return v, v, v
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    v = int(v * 255)
    t = int(t * 255)
    p = int(p * 255)
    q = int(q * 255)
    i = i % 6
    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    return v, p, q


def debounce(button, debounce_ms=200):
    global last_button_press
    try:
        value = button.value() == 0
        if value and time.ticks_ms() - last_button_press > debounce_ms:
            last_button_press = time.ticks_ms()
            return True
    except NameError:
        last_button_press = time.ticks_ms()
    return False


def get_applications() -> list[dict[str, str]]:
    # fetch a list of the applications that are stored in the filesystem
    applications = []
    for file in listdir():
        if file.endswith(".py") and file != "main.py":
            # convert the filename from "something_or_other.py" to "Something Or Other"
            # via weird incantations and a sprinkling of voodoo
            title = " ".join([v[:1].upper() + v[1:] for v in file[:-3].split("_")])

            applications.append(
                {
                    "file": file,
                    "title": title
                }
            )

    # sort the application list alphabetically by title and return the list
    return sorted(applications, key=lambda x: x["title"])


def prepare_for_launch() -> None:
    for k in locals().keys():
        if k not in ("__name__",
                     "application_file_to_launch",
                     "gc"):
            del locals()[k]
    gc.collect()


def menu() -> str:
    applications = get_applications()

    display.set_backlight(1.0)

    selected_item = 2
    scroll_position = 2
    target_scroll_position = 2

    selected_pen = WHITE
    unselected_pen = WHITE
    shadow_pen = BLACK

    # Set layer to 0 and decode the background PNG.
    display.set_layer(0)
    p = pngdec.PNG(display)
    p.open_file("backgroundforscreen.png")
    p.decode(0, 0)

    while True:

        if debounce(button_x):
            target_scroll_position -= 1
            target_scroll_position = target_scroll_position if target_scroll_position >= 0 else len(applications) - 1

        if debounce(button_z):
            target_scroll_position += 1
            target_scroll_position = target_scroll_position if target_scroll_position < len(applications) else 0

        if debounce(button_y):
            return applications[selected_item]["file"]

        scroll_position += (target_scroll_position - scroll_position) / 5

        # work out which item is selected (closest to the current scroll position)
        selected_item = round(target_scroll_position)

        # Set the layer to 1. We'll make all of our changes on this layer.
        display.set_layer(1)
        display.set_pen(BLACK)
        display.clear()

        # Draw some markers on screen so you know which buttons to press :)
        display.set_pen(WHITE)
        display.triangle(303, 42, 293, 55, 313, 55)
        display.rectangle(295, 114, 16, 16)
        display.triangle(303, 205, 293, 191, 313, 191)

        for list_index, application in enumerate(applications):
            distance = list_index - scroll_position

            text_size = 4 if selected_item == list_index else 2

            # center text horizontally
            text_x = 10

            row_height = text_size * 5 + 20

            # center list items vertically
            text_y = int(90 + distance * row_height - (row_height / 2))

            # draw the text, selected item brightest and with shadow
            if selected_item == list_index:
                display.set_pen(shadow_pen)
                display.text(application["title"], text_x + 1, text_y + 1, -1, text_size)

            text_pen = selected_pen if selected_item == list_index else unselected_pen
            display.set_pen(text_pen)
            display.text(application["title"], text_x, text_y, -1, text_size)

        display.update()


# The application we will be launching. This should be ouronly global, so we can
# drop everything else.
application_file_to_launch = menu()

# Run whatever we've set up to.
# If this fails, we'll exit the script and drop to the REPL, which is
# fairly reasonable.
prepare_for_launch()
__import__(application_file_to_launch)

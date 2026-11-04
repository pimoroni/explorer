"""
A gallery that shows all the .jpg and .png files saved to your Explorer.

Use X and Y to cycle through images
Z shows/hides the filename
A and B change the background colour (for .png files with transparency)
"""

import os
import jpegdec
import pngdec
from explorer import display, WHITE, BLACK, button_a, button_b, button_x, button_y, button_z
import gc

WIDTH, HEIGHT = display.get_bounds()

TOTAL_IMAGES = 0

jpeg = jpegdec.JPEG(display)
png = pngdec.PNG(display)

# Clear all layers first
display.set_pen(BLACK)
display.set_layer(0)
display.clear()
display.set_layer(1)
display.clear()

# Load images
try:
    IMAGES = [f for f in os.listdir("/") if f.endswith((".jpg", ".png"))]
    TOTAL_IMAGES = len(IMAGES)
except OSError:
    pass

CURRENT_IMAGE = 0
SHOW_INFO = True

BACKGROUND = WHITE


def show_image(n):
    gc.collect()
    file = IMAGES[n]
    name, ext = file.split(".")

    display.set_pen(BACKGROUND)
    display.clear()

    try:
        png.open_file("/{}".format(file))
        png.decode()
    except (OSError, RuntimeError):
        jpeg.open_file("/{}".format(file))
        jpeg.decode()

    if SHOW_INFO is True:
        label = f"{name} ({ext})"
        name_length = display.measure_text(label, 0.5)
        display.set_pen(BLACK)
        display.rectangle(0, HEIGHT - 21, name_length + 11, 21)
        display.set_pen(WHITE)
        display.rectangle(0, HEIGHT - 20, name_length + 10, 20)
        display.set_pen(BLACK)
        display.text(label, 5, HEIGHT - 10, WIDTH, 0.5)

        for i in range(TOTAL_IMAGES):
            x = WIDTH - 10
            y = int((HEIGHT / 2) - (TOTAL_IMAGES * 10 / 2) + (i * 10))
            display.set_pen(BLACK)
            display.rectangle(x, y, 8, 8)
            if CURRENT_IMAGE != i:
                display.set_pen(WHITE)
                display.rectangle(x + 1, y + 1, 6, 6)

    display.update()


changed = True

if TOTAL_IMAGES == 0:
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(WHITE)
    display.text("To run this demo, upload some .jpg or .png files to Explorer.", 0, 0, WIDTH, 3)
    display.update()

else:
    while True:
        if button_x.value() == 0:
            if CURRENT_IMAGE > 0:
                CURRENT_IMAGE -= 1
                changed = True

        if button_y.value() == 0:
            if CURRENT_IMAGE < TOTAL_IMAGES - 1:
                CURRENT_IMAGE += 1
                changed = True

        if button_a.value() == 0:
            BACKGROUND = WHITE
            changed = True

        if button_b.value() == 0:
            BACKGROUND = BLACK
            changed = True

        if button_z.value() == 0:
            SHOW_INFO = not SHOW_INFO
            changed = True

        if changed:
            show_image(CURRENT_IMAGE)
            changed = False

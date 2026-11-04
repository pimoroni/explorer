"""
Connect an old school four legged RGB LED up to Explorer and toggle the Red, Green and Blue channels with buttons A, B and C.
Press X for rainbows!

Position your LED so the long leg is pin 2 - this leg should be connected to ground.
The other three legs (pins 1, 3 and 4) are R, G and B - these should be wired to GP0, GP1 and GP2.
(Note that you don't need to include resistors in your circuit with Explorer, as there are resistors on the board).
"""
import time
from explorer import display, button_a, button_b, button_c, button_x, BLACK, WHITE
from pimoroni import RGBLED


# From CPython Lib/colorsys.py
def hsv_to_rgb(h, s, v):
    if s == 0.0:
        return v, v, v
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
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


# Set up an old school 4 pin RGB LED connected to GP0, GP1 and GP2
led = RGBLED(0, 1, 2, invert=False)

# Variables to keep track of rainbows
rainbow_mode = False
h = 0

# Clear all layers first
display.set_layer(0)
display.set_pen(BLACK)
display.clear()
display.set_layer(1)
display.set_pen(BLACK)
display.clear()

# Set the layer we're going to be drawing to.
display.set_layer(0)

# Draw some text to the screen
display.set_pen(WHITE)
display.text("Wire an RGB LED up to GP0, GP1 and GP2, and then press A, B, C or X", 0, 0, 320, 4)
display.update()

while True:
    # Toggle rainbow mode if button X is pushed
    if button_x.value() == 0:
        rainbow_mode = not rainbow_mode
    if rainbow_mode is True:  # then apply rainbow magic
        h += 1
        r, g, b = [int(255 * c) for c in hsv_to_rgb(h / 360.0, 1.0, 1.0)]
        led.set_rgb(r, g, b)

    # Because we're using Pin.PULL_UP the logic is reversed - '0' is pushed and '1' is unpushed
    else:
        led.set_rgb(0, 0, 0)
        if button_a.value() == 0:  # set LED to red
            led.set_rgb(255, 0, 0)
        if button_b.value() == 0:  # set LED to blue
            led.set_rgb(0, 255, 0)
        if button_c.value() == 0:  # set LED to green
            led.set_rgb(0, 0, 255)
    # Short pause to stop Thonny from falling over
    time.sleep(0.01)

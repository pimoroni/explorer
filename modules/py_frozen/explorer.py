from picographics import PicoGraphics, DISPLAY_EXPLORER, PEN_RGB565
from machine import Pin
from micropython import const

# We're only using a few colours so we can use a 4 bit/16 colour palette and save RAM!
display = PicoGraphics(display=DISPLAY_EXPLORER, pen_type=PEN_RGB565)

BUTTON_A_PIN = const(16)
BUTTON_B_PIN = const(15)
BUTTON_C_PIN = const(14)
BUTTON_X_PIN = const(17)
BUTTON_Y_PIN = const(18)
BUTTON_Z_PIN = const(19)

BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
CYAN = display.create_pen(0, 255, 255)
MAGENTA = display.create_pen(255, 0, 255)
YELLOW = display.create_pen(255, 255, 0)
RED = display.create_pen(255, 0, 0)
GREEN = display.create_pen(0, 255, 0)
BLUE = display.create_pen(0, 0, 255)

_button_a = Pin(BUTTON_A_PIN, Pin.IN, Pin.PULL_UP)
_button_b = Pin(BUTTON_B_PIN, Pin.IN, Pin.PULL_UP)
_button_c = Pin(BUTTON_C_PIN, Pin.IN, Pin.PULL_UP)
_button_x = Pin(BUTTON_X_PIN, Pin.IN, Pin.PULL_UP)
_button_y = Pin(BUTTON_Y_PIN, Pin.IN, Pin.PULL_UP)
_button_z = Pin(BUTTON_Z_PIN, Pin.IN, Pin.PULL_UP)

_exports = {
    "BLACK": BLACK,
    "WHITE": WHITE,
    "CYAN": CYAN,
    "MAGENTA": MAGENTA,
    "YELLOW": YELLOW,
    "RED": RED,
    "GREEN": GREEN,
    "BLUE": BLUE,
    "text": display.text,
    "pen": display.set_pen
}
import machine
import sys
import time
from io import StringIO

import _input
import st7789
from picovector import color, font, image, rect

from .buttons import (  # noqa: F401
    BACK,
    DOWN,
    HOME,
    SELECT,
    UP,
    Button,
    button_a,
    button_b,
    button_c,
    button_user,
    button_x,
    button_y,
    button_z,
    buttons,
    held,
    pressed,
    released,
    rotate_buttons,
)
from .io import (  # noqa: F401
    ADC0,
    ADC1,
    ADC2,
    ADC3,
    ADC4,
    ADC5,
    GP0,
    GP1,
    GP2,
    GP3,
    GP4,
    GP5,
    Analog,
    Input,
    Output,
    beep,
    i2c,
    play_tone,
    servo,
    stop_tone,
    volume,
)
from . import io as _io

WIDTH = 320
HEIGHT = 240

display = st7789.ST7789()
display.fullres(True)
screen = image(WIDTH, HEIGHT, memoryview(display), image.RGB565)
screen.font = font.sins


def backlight(level):
    display.backlight(min(1.0, max(0.0, level)))


def rotate(upside_down):
    display.set_rotate_180(upside_down)
    rotate_buttons(upside_down)


def poll():
    _input.poll()
    _io.poll_inputs()


def update():
    display.update()
    poll()


def ticks():
    return _input.ticks


def delta():
    return _input.ticks_delta


def _format_exception(error):
    buffer = StringIO()
    sys.print_exception(error, buffer)
    return buffer.getvalue()


def sensor(factory, title_font=None, on_disconnect=None):
    from .stick import Sensor

    return Sensor(sys.modules[__name__], factory, title_font, on_disconnect)


def show_error(title, message):
    print(f"{title}\n{message}")
    screen.pen = color.rgb(120, 20, 20)
    screen.clear()
    screen.pen = color.rgb(255, 255, 255)
    screen.text(title, 8, 6)
    screen.pen = color.rgb(255, 210, 210)
    screen.text(message, rect(8, 34, WIDTH - 16, HEIGHT - 60))
    screen.pen = color.rgb(255, 255, 255)
    screen.text("Press any button", 8, HEIGHT - 20)
    update()
    while True:
        poll()
        if pressed():
            break
        time.sleep_ms(10)
    while held():
        poll()
        time.sleep_ms(10)


def _return_home(_pin):
    while not button_user.pin.value():
        pass
    machine.reset()


def launch(path):
    folder = path.rsplit("/", 1)[0] or "/"
    button_user.pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=_return_home)
    try:
        with open(path) as source_file:
            source = source_file.read()
        sys.path.insert(0, folder)
        exec(compile(source, path, "exec"), {"__name__": "__main__", "__file__": path})
    except KeyboardInterrupt:
        button_user.pin.irq(handler=None)
        _io.release_all()
        raise
    except Exception as error:  # noqa: BLE001
        show_error("Error!", _format_exception(error))
    machine.reset()

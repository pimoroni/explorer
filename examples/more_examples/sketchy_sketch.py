# This example is an adaptation of the program sketchy_sketch.py from the pimoroni-pico tufty2040 repository for the Pimoroni Explorer
# button x: up button_y: down button c: left button z: right  button a: reset the screen
import time

from explorer import button_a,button_b,button_c,button_x,button_y,button_z
from picographics import PicoGraphics, DISPLAY_EXPLORER,PEN_RGB332


display = PicoGraphics(display=DISPLAY_EXPLORER, pen_type=PEN_RGB332)

button_up = button_x
button_down = button_y

WIDTH, HEIGHT = 320, 240
display.set_backlight(1.0)



def draw_area():
    display.set_pen(display.create_pen(200, 0, 0))
    display.clear()

    display.set_pen(display.create_pen(255, 215, 0))
    display.text("Sketchy-Sketch", 90, 5, 0, 2)

    # draw main surface
    display.set_pen(display.create_pen(205, 205, 205))
    display.rectangle(25, 25, 270, 180)

    # draw knobs
    display.set_pen(display.create_pen(150, 50, 50))
    display.circle(25 + 5, 225 + 5, 20)
    display.circle(295 + 5, 225 + 5, 20)
    display.set_pen(display.create_pen(255, 255, 255))
    display.circle(25 - 1, 225 - 1, 16)
    display.circle(295 - 1, 225 - 1, 16)
    display.set_pen(display.create_pen(155, 155, 155))
    display.circle(25 + 1, 225 + 1, 16)
    display.circle(295 + 1, 225 + 1, 16)
    display.set_pen(display.create_pen(205, 205, 205))
    display.circle(25, 225, 15)
    display.circle(295, 225, 15)


# start position for drawing cursor
position_x = 160
position_y = 110

# draw the sketchy sketch
draw_area()

while True:
    # check for user input and update cursor position as needed
    if button_z.value() == 0 and position_x < 290:
        position_x += 1

    if button_c.value() == 0 and position_x > 30:
        position_x -= 1

    if button_up.value() == 0 and position_y > 30:
        position_y -= 1

    if button_down.value() == 0 and position_y < 200:
        position_y += 1

    if button_a.value() == 0:
        draw_area()

    # draw the line
    display.set_pen(display.create_pen(50, 50, 50))
    display.circle(position_x, position_y, 2)

    # update the screen contents
    display.update()

    time.sleep(0.005)

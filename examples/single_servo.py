"""
Demonstrates how to control a single servo on Explorer.
"""
import time
import math
from explorer import display, servos, SERVO_1, button_a, BLACK, WHITE
from micropython import const

BG = display.create_pen(255, 99, 71)
SWEEPS = const(3)                     # How many sweeps of the servo to perform
STEPS = const(10)                     # The number of discrete sweep steps
STEPS_INTERVAL = const(0.5)           # The time in seconds between each step of the sequence
SWEEP_EXTENT = const(90.0)            # How far from zero to move the servo when sweeping


# A little function to save ourselves some time doing the drop shadows :)
def drop_shadow_text(text, x, y, offset, wrap, size, main_colour):

    # Draw the drop shadow
    display.set_pen(BLACK)
    display.text(text, x + offset, y + offset, wrap, size)

    # Draw the main text
    display.set_pen(main_colour)
    display.text(text, x, y, wrap, size)


def clear():
    display.set_pen(BG)
    display.clear()


# Clear all layers first
display.set_layer(0)
display.set_pen(BLACK)
display.clear()
display.set_layer(1)
display.set_pen(BLACK)
display.clear()

# Set the layer we're going to be drawing to.
display.set_layer(0)

# Clear the screen and draw the prompt
clear()
drop_shadow_text("Attach a servo to slot 1!\n\nPress A to start", 10, 75, 3, 320, 3, WHITE)
display.update()

# We'll wait here until the user presses the A button
while (button_a.value()):
    pass

# Access the servo from Explorer and enable it (this puts it at the middle)
s = servos[SERVO_1]
clear()
drop_shadow_text("Enabling Servo...", 10, 75, 3, 320, 3, WHITE)
display.update()
s.enable()
time.sleep(2)

# Go to min
clear()
drop_shadow_text("Go to min", 10, 75, 3, 320, 3, WHITE)
display.update()
s.to_min()
time.sleep(2)

# Go to max
clear()
drop_shadow_text("Go to max", 10, 75, 3, 320, 3, WHITE)
display.update()
s.to_max()
time.sleep(2)

# Go back to mid
clear()
drop_shadow_text("Back to the middle", 10, 75, 3, 320, 3, WHITE)
display.update()
s.to_mid()
time.sleep(2)

# Do a sine sweep
clear()
drop_shadow_text(f"Do {SWEEPS} sine sweeps", 10, 75, 3, 320, 3, WHITE)
display.update()
for _ in range(SWEEPS):
    for i in range(360):
        s.value(math.sin(math.radians(i)) * SWEEP_EXTENT)
        time.sleep(0.02)

# Do a stepped sweep
clear()
drop_shadow_text(f"Do {SWEEPS} stepped sweeps", 10, 75, 3, 320, 3, WHITE)
display.update()
for _ in range(SWEEPS):
    for i in range(STEPS):
        s.to_percent(i, 0, STEPS, 0.0 - SWEEP_EXTENT, SWEEP_EXTENT)
        time.sleep(STEPS_INTERVAL)
    for i in range(STEPS):
        s.to_percent(i, STEPS, 0, 0.0 - SWEEP_EXTENT, SWEEP_EXTENT)
        time.sleep(STEPS_INTERVAL)

# Disable the servo
clear()
drop_shadow_text("Disable servo ", 10, 75, 3, 320, 3, WHITE)
display.update()
s.disable()

clear()
drop_shadow_text("Done!", 10, 75, 3, 320, 3, WHITE)
display.update()

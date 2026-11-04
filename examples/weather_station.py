# Plug a Multi Sensor stick into your Pimoroni Explorer and make a little indoor weather station, with barometer style descriptions.

import time
from breakout_bme280 import BreakoutBME280
from explorer import display, i2c, BLACK, WHITE, RED
import jpegdec

# Clear all layers first
display.set_layer(0)
display.set_pen(BLACK)
display.clear()
display.set_layer(1)
display.set_pen(BLACK)
display.clear()

try:
    bme = BreakoutBME280(i2c, address=0x76)
except RuntimeError:
    display.set_layer(0)
    display.set_pen(RED)
    display.clear()
    display.set_pen(WHITE)
    display.text("Multi-Sensor stick not detected! :(", 10, 95, 320, 3)
    display.update()

# set up some pen colours to make drawing easier
TEMPCOLOUR = display.create_pen(0, 0, 0)  # this colour will get changed in a bit
GREY = display.create_pen(125, 125, 125)


# converts the temperature into a barometer-type description and pen colour
def describe_temperature(temperature):
    global TEMPCOLOUR
    if temperature < 10:
        description = "very cold"
        TEMPCOLOUR = display.create_pen(0, 255, 255)
    elif 10 <= temperature < 20:
        description = "cold"
        TEMPCOLOUR = display.create_pen(0, 0, 255)
    elif 20 <= temperature < 25:
        description = "temperate"
        TEMPCOLOUR = display.create_pen(0, 255, 0)
    elif 25 <= temperature < 30:
        description = "warm"
        TEMPCOLOUR = display.create_pen(255, 255, 0)
    elif temperature >= 30:
        description = "very warm"
        TEMPCOLOUR = display.create_pen(255, 0, 0)
    else:
        description = ""
        TEMPCOLOUR = display.create_pen(0, 0, 0)
    return description


# comment out the function above and uncomment this one for yorkshire mode
"""
def describe_temperature(temperature):
    global TEMPCOLOUR
    if temperature < 10:
        description = "frozzed"
        TEMPCOLOUR = display.create_pen(0, 255, 255)
    elif 10 <= temperature < 20:
        description = "nithering"
        TEMPCOLOUR = display.create_pen(0, 0, 255)
    elif 20 <= temperature < 25:
        description = "fair t' middlin"
        TEMPCOLOUR = display.create_pen(0, 255, 0)
    elif 25 <= temperature < 30:
        description = "chuffing warm"
        TEMPCOLOUR = display.create_pen(255, 255, 0)
    elif temperature >= 30:
        description = "crackin t' flags"
        TEMPCOLOUR = display.create_pen(255, 0, 0)
    else:
        description = ""
        TEMPCOLOUR = display.create_pen(0, 0, 0)
    return description
"""


# converts pressure into barometer-type description
def describe_pressure(pressure):
    if pressure < 970:
        description = "storm"
    elif 970 <= pressure < 990:
        description = "rain"
    elif 990 <= pressure < 1010:
        description = "change"
    elif 1010 <= pressure < 1030:
        description = "fair"
    elif pressure >= 1030:
        description = "dry"
    else:
        description = ""
    return description


# converts humidity into good/bad description
def describe_humidity(humidity):
    if 40 < humidity < 60:
        description = "good"
    else:
        description = "bad"
    return description


# Create a new JPEG decoder for our PicoGraphics
j = jpegdec.JPEG(display)

background_jpg = False

try:
    j.open_file("backgroundforscreen.jpg")
    background_jpg = True
except OSError:
    print("Background not found - copy backgroundforscreen.jpg to your Explorer")

# attempt to display a fancy background, if the file is present
# The background is drawn on layer 0
if background_jpg is True:
    display.set_layer(0)
    j.decode(0, 0, jpegdec.JPEG_SCALE_FULL, dither=True)
else:
    display.set_pen(BLACK)
    display.clear()

while True:

    # Switch the layer 1. This is where we'll draw our screen updates
    display.set_layer(1)

    display.set_pen(BLACK)
    display.clear()

    # read the sensors
    temperature, pressure, humidity = bme.read()
    # pressure comes in pascals which is a reight long number, lets convert it to the more manageable hPa
    pressurehpa = pressure / 100

    # draw a thermometer/barometer thingy
    display.set_pen(GREY)
    display.circle(250, 175, 40)
    display.rectangle(240, 30, 20, 140)

    # switch to red to draw the 'mercury'
    display.set_pen(RED)
    display.circle(250, 175, 30)
    thermometerheight = int(120 / 30 * temperature)
    if thermometerheight > 120:
        thermometerheight = 120
    if thermometerheight < 1:
        thermometerheight = 1
    display.rectangle(245, 155 - thermometerheight, 10, thermometerheight)

    # drawing the temperature text
    display.set_pen(WHITE)
    display.text("temperature:", 10, 10, 240, 3)
    display.set_pen(TEMPCOLOUR)
    display.text("{:.1f}".format(temperature) + "C", 10, 30, 240, 5)
    display.set_pen(WHITE)
    display.text(describe_temperature(temperature), 10, 60, 240, 3)

    # and the pressure text
    display.text("pressure:", 10, 85, 240, 3)
    display.text("{:.0f}".format(pressurehpa) + "hPa", 10, 105, 240, 5)
    display.text(describe_pressure(pressurehpa), 10, 135, 240, 3)

    # and the humidity text
    display.text("humidity:", 10, 160, 240, 3)
    display.text("{:.0f}".format(humidity) + "%", 10, 180, 240, 5)
    display.text(describe_humidity(humidity), 10, 210, 240, 3)

    # time to update the display
    display.update()

    # wait for a short time to stop Thonny from freaking out
    time.sleep(0.1)

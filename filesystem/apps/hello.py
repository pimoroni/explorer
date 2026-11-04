"""Hello
Draw your first shapes.

Icon: waving_hand
"""
import explorer
from explorer import screen
from picovector import color, shape

colours = [color.rgb(226, 83, 29), color.rgb(52, 199, 89), color.rgb(47, 123, 255)]


while True:
    screen.pen = color.rgb(18, 24, 38)
    screen.clear()

    t = explorer.ticks() / 1000
    for index, colour in enumerate(colours):
        screen.pen = colour
        x = 60 + index * 100
        y = 140 + int(30 * ((t * 2 + index) % 2 - 1) ** 2)
        screen.shape(shape.circle(x, y, 30))

    screen.pen = color.rgb(255, 255, 255)
    screen.text("Hello, Explorer!", 90, 40)

    explorer.update()

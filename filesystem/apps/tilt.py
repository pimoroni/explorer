"""Level
Tilt to roll the bubble.

You will need:
- Sensor stick

Icon: straighten
"""
import math

import explorer
from explorer import screen
from lsm6ds3 import LSM6DS3
from picovector import color, shape

imu = explorer.sensor(LSM6DS3)
bubble_x = 160.0
bubble_y = 120.0

while True:
    ax, ay, az, gx, gy, gz = imu.get_readings()
    pitch = math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))
    roll = math.degrees(math.atan2(ay, az))
    target_x = 160 - max(-90, min(90, roll))
    target_y = 120 - max(-90, min(90, pitch))
    bubble_x += (target_x - bubble_x) * 0.3
    bubble_y += (target_y - bubble_y) * 0.3

    screen.pen = color.rgb(18, 24, 38)
    screen.clear()
    screen.pen = color.rgb(50, 60, 80)
    screen.shape(shape.circle(160, 120, 100))
    screen.pen = color.rgb(18, 24, 38)
    screen.shape(shape.circle(160, 120, 96))
    screen.pen = color.rgb(52, 199, 89)
    screen.shape(shape.circle(int(bubble_x), int(bubble_y), 18))
    screen.pen = color.rgb(255, 255, 255)
    screen.text(f"pitch {pitch:.0f}  roll {roll:.0f}", 10, 10)

    explorer.update()

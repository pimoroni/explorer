import json
import math
import time

CALIBRATION_FILE = "/robot.json"
DEFAULTS = {"balance": 0.0}
LEFT_SERVO = 1
RIGHT_SERVO = 2
GYRO_DPS = 0.00875
SETTLE_MS = 500
SETTLE_GAP_MS = 10


def load():
    settings = dict(DEFAULTS)
    try:
        with open(CALIBRATION_FILE) as calibration_file:
            settings.update(json.load(calibration_file))
    except (OSError, ValueError):
        pass
    return settings


def save(settings):
    with open(CALIBRATION_FILE, "w") as calibration_file:
        json.dump(settings, calibration_file)


class Robot:
    def __init__(self, explorer, speed=0.6):
        from servo import CONTINUOUS

        self.left_wheel = explorer.servo(LEFT_SERVO, CONTINUOUS)
        self.right_wheel = explorer.servo(RIGHT_SERVO, CONTINUOUS)
        self.speed = speed
        self.settings = load()
        self.stop()

    def drive(self, left, right):
        balance = self.settings["balance"]
        left *= 1 - max(0.0, -balance)
        right *= 1 - max(0.0, balance)
        self._set(self.left_wheel, left * self.speed)
        self._set(self.right_wheel, -right * self.speed)

    def stop(self):
        self.left_wheel.disable()
        self.right_wheel.disable()

    @staticmethod
    def _set(wheel, value):
        if value == 0:
            wheel.disable()
        else:
            wheel.value(max(-1.0, min(1.0, value)))


class Heading:
    def __init__(self, imu):
        self.imu = imu
        self.up = (0.0, 0.0, 1.0)
        self.bias = (0.0, 0.0, 0.0)
        self.heading = 0.0
        self.rate = 0.0
        self.tilt = 0.0
        self.last = time.ticks_ms()

    def settle(self):
        totals = [0.0] * 6
        count = 0
        started = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), started) < SETTLE_MS:
            for index, value in enumerate(self.imu.get_readings()):
                totals[index] += value
            count += 1
            time.sleep_ms(SETTLE_GAP_MS)
        means = [total / count for total in totals]
        length = math.sqrt(sum(value * value for value in means[:3])) or 1
        self.up = tuple(value / length for value in means[:3])
        self.bias = tuple(means[3:])
        self.heading = 0.0
        self.rate = 0.0
        self.tilt = 0.0
        self.last = time.ticks_ms()

    def update(self):
        ax, ay, az, gx, gy, gz = self.imu.get_readings()
        now = time.ticks_ms()
        elapsed = time.ticks_diff(now, self.last) / 1000
        self.last = now
        up_x, up_y, up_z = self.up
        bias_x, bias_y, bias_z = self.bias
        self.rate = ((gx - bias_x) * up_x + (gy - bias_y) * up_y + (gz - bias_z) * up_z) * GYRO_DPS
        self.heading += self.rate * elapsed
        length = math.sqrt(ax * ax + ay * ay + az * az) or 1
        alignment = max(-1.0, min(1.0, (ax * up_x + ay * up_y + az * up_z) / length))
        self.tilt = math.degrees(math.acos(alignment))
        return self.heading

import machine
import time
from micropython import const

GP0 = const(0)
GP1 = const(1)
GP2 = const(2)
GP3 = const(3)
GP4 = const(4)
GP5 = const(5)

ADC0 = const(40)
ADC1 = const(41)
ADC2 = const(42)
ADC3 = const(43)
ADC4 = const(44)
ADC5 = const(45)

SERVO_PINS = (9, 8, 7, 6)

AUDIO_PIN = const(12)
AMP_EN_PIN = const(13)

I2C_SDA_PIN = const(20)
I2C_SCL_PIN = const(21)

PWM_FREQUENCY = const(1000)

DEBOUNCE_MS = const(30)

SPEAKER_MAX_DUTY = const(512)

_inputs = []


class Output:
    def __init__(self, pin, value=0):
        self._number = pin
        self._pin = machine.Pin(pin, machine.Pin.OUT, value=value)
        self._pwm = None
        self._value = 1 if value else 0

    def _digital(self):
        if self._pwm is not None:
            self._pwm.deinit()
            self._pwm = None
            self._pin = machine.Pin(self._number, machine.Pin.OUT)

    def value(self, value=None):
        if value is None:
            return self._value
        self._digital()
        self._value = 1 if value else 0
        self._pin.value(self._value)
        return None

    def on(self):
        self.value(1)

    def off(self):
        self.value(0)

    def toggle(self):
        self.value(not self._value)

    def brightness(self, level=None):
        if level is None:
            if self._pwm is None:
                return float(self._value)
            return self._pwm.duty_u16() / 65535
        level = min(1.0, max(0.0, level))
        if self._pwm is None:
            self._pwm = machine.PWM(self._pin, freq=PWM_FREQUENCY)
        self._pwm.duty_u16(int(level * 65535))
        self._value = 1 if level > 0 else 0
        return None


class Input:
    def __init__(self, pin, pull=machine.Pin.PULL_UP):
        self._pin = machine.Pin(pin, machine.Pin.IN, pull)
        self._active = 0 if pull == machine.Pin.PULL_UP else 1
        self._held = False
        self._changed = False
        self._changed_at = time.ticks_ms()
        _inputs.append(self)

    def value(self):
        return self._pin.value()

    def update(self):
        now = time.ticks_ms()
        held = self._pin.value() == self._active
        self._changed = held != self._held and time.ticks_diff(now, self._changed_at) >= DEBOUNCE_MS
        if self._changed:
            self._held = held
            self._changed_at = now

    @property
    def held(self):
        return self._held

    @property
    def pressed(self):
        return self._held and self._changed

    @property
    def released(self):
        return self._changed and not self._held


class Analog:
    def __init__(self, pin):
        self._adc = machine.ADC(machine.Pin(pin))

    def read_u16(self):
        return self._adc.read_u16()

    def read(self):
        return self._adc.read_u16() / 65535

    def voltage(self):
        return self._adc.read_u16() * 3.3 / 65535


def servo(number, calibration=None):
    from servo import Servo, ANGULAR

    if not 1 <= number <= len(SERVO_PINS):
        raise ValueError("servo number must be 1 to 4")
    return Servo(SERVO_PINS[number - 1], ANGULAR if calibration is None else calibration)


_audio = None
_amp = None
_volume = 0.5
_tone_ends = None


def _audio_setup():
    global _audio, _amp
    if _audio is None:
        _amp = machine.Pin(AMP_EN_PIN, machine.Pin.OUT, value=0)
        _audio = machine.PWM(machine.Pin(AUDIO_PIN))
    return _audio


def volume(level=None):
    global _volume
    if level is None:
        return _volume
    _volume = min(1.0, max(0.0, level))
    return None


def play_tone(frequency, level=None):
    global _tone_ends
    _tone_ends = None
    audio = _audio_setup()
    audio.freq(int(frequency))
    level = _volume if level is None else min(1.0, max(0.0, level))
    audio.duty_u16(int(SPEAKER_MAX_DUTY * level * level))
    _amp.on()


def beep(frequency, duration=40, level=None):
    global _tone_ends
    play_tone(frequency, level)
    _tone_ends = time.ticks_add(time.ticks_ms(), duration)


def stop_tone():
    global _tone_ends
    _tone_ends = None
    if _audio is not None:
        _audio.duty_u16(0)
        _amp.off()


_i2c = None


def i2c():
    global _i2c
    if _i2c is None:
        from pimoroni_i2c import PimoroniI2C

        _i2c = PimoroniI2C(I2C_SDA_PIN, I2C_SCL_PIN, 100000)
    return _i2c


def poll_inputs():
    for watched in _inputs:
        watched.update()
    if _tone_ends is not None and time.ticks_diff(time.ticks_ms(), _tone_ends) >= 0:
        stop_tone()


def release_all():
    _inputs.clear()
    stop_tone()

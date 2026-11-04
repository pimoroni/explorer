from machine import Pin, PWM
from pimoroni_i2c import PimoroniI2C
from servo import Servo
from picographics import PicoGraphics, DISPLAY_EXPLORER, PEN_RGB565
from micropython import const

# Enable layer support in PicoGraphics
LAYERS = True

# Index Constants
SERVO_1 = const(0)
SERVO_2 = const(1)
SERVO_3 = const(2)
SERVO_4 = const(3)

# Count Constants
NUM_GPIOS = const(6)
NUM_ADCS = const(6)
NUM_SERVOS = const(4)
NUM_SWITCHES = const(6)

# Colours!
WHITE = const(65535)
BLACK = const(0)
CYAN = const(65287)
MAGENTA = const(8184)
YELLOW = const(57599)
GREEN = const(57351)
RED = const(248)
BLUE = const(7936)

SWITCH_A_PIN = const(16)
SWITCH_B_PIN = const(15)
SWITCH_C_PIN = const(14)
SWITCH_X_PIN = const(17)
SWITCH_Y_PIN = const(18)
SWITCH_Z_PIN = const(19)
SWITCH_USER_PIN = const(22)

I2C_SDA_PIN = const(20)
I2C_SCL_PIN = const(21)

SERVO_1_PIN = const(9)
SERVO_2_PIN = const(8)
SERVO_3_PIN = const(7)
SERVO_4_PIN = const(6)

ADC_0_PIN = const(40)
ADC_1_PIN = const(41)
ADC_2_PIN = const(42)
ADC_3_PIN = const(43)
ADC_4_PIN = const(44)
ADC_5_PIN = const(45)

GPIO_0_PIN = const(0)
GPIO_1_PIN = const(1)
GPIO_2_PIN = const(2)
GPIO_3_PIN = const(3)
GPIO_4_PIN = const(4)
GPIO_5_PIN = const(5)

PWM_AUDIO_PIN = const(12)
AMP_EN_PIN = const(13)

AMP_CORRECTION = const(4)
DEFAULT_VOLUME = const(0.2)

# Set up the i2c for Qw/st and Breakout Garden
i2c = PimoroniI2C(I2C_SDA_PIN, I2C_SCL_PIN, 100000)

# Set up the amp
_amp_en = Pin(AMP_EN_PIN, Pin.OUT)
_amp_en.off()

audio_pwm = PWM(Pin(PWM_AUDIO_PIN))
_volume = DEFAULT_VOLUME

# Setup the pins for the buttons
button_a = Pin(SWITCH_A_PIN, Pin.IN, Pin.PULL_UP)
button_b = Pin(SWITCH_B_PIN, Pin.IN, Pin.PULL_UP)
button_c = Pin(SWITCH_C_PIN, Pin.IN, Pin.PULL_UP)
button_x = Pin(SWITCH_X_PIN, Pin.IN, Pin.PULL_UP)
button_y = Pin(SWITCH_Y_PIN, Pin.IN, Pin.PULL_UP)
button_z = Pin(SWITCH_Z_PIN, Pin.IN, Pin.PULL_UP)
button_user = Pin(SWITCH_USER_PIN, Pin.IN)

# Setup the display
display = PicoGraphics(display=DISPLAY_EXPLORER, pen_type=PEN_RGB565, layers=2 if LAYERS else 1)

# setup servos
servos = [Servo(SERVO_1_PIN - i) for i in range(4)]


def play_tone(frequency):
    try:
        audio_pwm.freq(frequency)
    except ValueError:
        play_silence()
        raise ValueError("frequency of range. Expected greater than 0") from None

    corrected_volume = (_volume ** 4)  # Correct for RC Filter curve
    audio_pwm.duty_u16(int(32768 * corrected_volume))
    mute_audio(False)


def play_silence():
    audio_pwm.freq(44100)

    corrected_volume = (_volume ** 4)  # Correct for RC Filter curve
    audio_pwm.duty_u16(int(32768 * corrected_volume))
    mute_audio(False)


def stop_playing():
    audio_pwm.duty_u16(0)
    mute_audio(True)


def set_volume(volume=None):
    global _volume
    if volume is None:
        return _volume

    if volume < 0.01 or volume > 1.0:
        raise ValueError("volume out of range. Expected 0.0 to 1.0")

    _volume = volume
    return None


def mute_audio(value=True):
    _amp_en.off() if value else _amp_en.on()

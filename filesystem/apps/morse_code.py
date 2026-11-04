"""Morse Code
Tap out letters with a switch.

You will need:
- Switch
- White LED
- 4 wires

Icon: cell_tower
"""
import explorer
from explorer import BACK, GP0, GP3, SELECT, Input, Output, labels, screen
from picovector import color, font, image, rect, shape

screen.antialias = image.X2

TITLE_FONT = font.load("/rom/fonts/manrope-800.af")
BODY_FONT = font.load("/rom/fonts/manrope-600.af")

INK = color.rgb(31, 29, 27)
PAPER = color.rgb(239, 235, 227)
DIM = color.rgb(125, 120, 112)
FAINT = color.rgb(58, 56, 53)
ACCENT = color.rgb(92, 150, 255)

DASH_MS = 250
LETTER_GAP_MS = 700
WORD_GAP_MS = 1600
TONE = 660
MAX_TEXT = 40

CODES = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E", "..-.": "F",
    "--.": "G", "....": "H", "..": "I", ".---": "J", "-.-": "K", ".-..": "L",
    "--": "M", "-.": "N", "---": "O", ".--.": "P", "--.-": "Q", ".-.": "R",
    "...": "S", "-": "T", "..-": "U", "...-": "V", ".--": "W", "-..-": "X",
    "-.--": "Y", "--..": "Z", ".----": "1", "..---": "2", "...--": "3",
    "....-": "4", ".....": "5", "-....": "6", "--...": "7", "---..": "8",
    "----.": "9", "-----": "0",
}

key = Input(GP3)
led = Output(GP0)
symbols = ""
text = ""
key_down_at = None
key_up_at = explorer.ticks()

while True:
    now = explorer.ticks()
    down = key.held or SELECT.held

    if down and key_down_at is None:
        key_down_at = now
        led.on()
        explorer.play_tone(TONE)
    elif not down and key_down_at is not None:
        symbols += "-" if now - key_down_at >= DASH_MS else "."
        key_down_at = None
        key_up_at = now
        led.off()
        explorer.stop_tone()

    if key_down_at is None:
        silence = now - key_up_at
        if symbols and silence > LETTER_GAP_MS:
            text = (text + CODES.get(symbols, "?"))[-MAX_TEXT:]
            symbols = ""
        elif text and not text.endswith(" ") and silence > WORD_GAP_MS:
            text += " "

    if BACK.pressed:
        text = ""
        symbols = ""

    screen.pen = INK
    screen.clear()

    screen.pen = FAINT
    screen.shape(shape.rounded_rectangle(72, 12, 236, 120, 12))
    screen.font = TITLE_FONT
    screen.pen = PAPER
    screen.text(text + "_", rect(84, 22, 212, 100), 24)

    x = 92
    for symbol in symbols:
        screen.pen = ACCENT
        if symbol == ".":
            screen.shape(shape.circle(x, 155, 8))
            x += 26
        else:
            screen.shape(shape.rounded_rectangle(x - 8, 147, 40, 16, 8))
            x += 50
    if key_down_at is not None:
        screen.pen = PAPER
        held = min(1.0, (now - key_down_at) / DASH_MS)
        screen.shape(shape.rounded_rectangle(x - 8, 147, 16 + 24 * held, 16, 8))

    guess = CODES.get(symbols, "")
    screen.font = TITLE_FONT
    screen.pen = DIM
    screen.text(guess, rect(248, 134, 60, 42), 40, align=(image.CENTER, image.MIDDLE))

    screen.font = BODY_FONT
    screen.pen = DIM
    screen.text("Short press dot, long press dash", 12, 184, 16)
    screen.text("LED GP0  Switch GP3", 12, 212, 14)

    actions = {"A": "Key"}
    if text or symbols:
        actions["B"] = "Clear"
    labels.draw(screen, TITLE_FONT, actions, None if text or symbols else "A")

    explorer.update()

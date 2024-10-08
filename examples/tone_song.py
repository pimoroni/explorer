import time
from explorer import display, play_silence, play_tone, set_volume, stop_playing, button_x, WHITE, BLACK

"""
This example shows you how you can use Explorer's audio output
with a speaker to play different notes and string them together into a bleepy tune.

It uses code written by Avram Piltch - check out his Tom's Hardware article!
https://www.tomshardware.com/uk/how-to/buzzer-music-raspberry-pi-pico

Press "X" button to start or stop the song.
"""

WIDTH, HEIGHT = display.get_bounds()
BG = display.create_pen(70, 130, 180)

# This handy list converts notes into frequencies, which you can use with the inventor.play_tone function
TONES = {
    "B0": 31,
    "C1": 33,
    "CS1": 35,
    "D1": 37,
    "DS1": 39,
    "E1": 41,
    "F1": 44,
    "FS1": 46,
    "G1": 49,
    "GS1": 52,
    "A1": 55,
    "AS1": 58,
    "B1": 62,
    "C2": 65,
    "CS2": 69,
    "D2": 73,
    "DS2": 78,
    "E2": 82,
    "F2": 87,
    "FS2": 93,
    "G2": 98,
    "GS2": 104,
    "A2": 110,
    "AS2": 117,
    "B2": 123,
    "C3": 131,
    "CS3": 139,
    "D3": 147,
    "DS3": 156,
    "E3": 165,
    "F3": 175,
    "FS3": 185,
    "G3": 196,
    "GS3": 208,
    "A3": 220,
    "AS3": 233,
    "B3": 247,
    "C4": 262,
    "CS4": 277,
    "D4": 294,
    "DS4": 311,
    "E4": 330,
    "F4": 349,
    "FS4": 370,
    "G4": 392,
    "GS4": 415,
    "A4": 440,
    "AS4": 466,
    "B4": 494,
    "C5": 523,
    "CS5": 554,
    "D5": 587,
    "DS5": 622,
    "E5": 659,
    "F5": 698,
    "FS5": 740,
    "G5": 784,
    "GS5": 831,
    "A5": 880,
    "AS5": 932,
    "B5": 988,
    "C6": 1047,
    "CS6": 1109,
    "D6": 1175,
    "DS6": 1245,
    "E6": 1319,
    "F6": 1397,
    "FS6": 1480,
    "G6": 1568,
    "GS6": 1661,
    "A6": 1760,
    "AS6": 1865,
    "B6": 1976,
    "C7": 2093,
    "CS7": 2217,
    "D7": 2349,
    "DS7": 2489,
    "E7": 2637,
    "F7": 2794,
    "FS7": 2960,
    "G7": 3136,
    "GS7": 3322,
    "A7": 3520,
    "AS7": 3729,
    "B7": 3951,
    "C8": 4186,
    "CS8": 4435,
    "D8": 4699,
    "DS8": 4978
}

# Put the notes for your song in here!
SONG = ("F6", "F6", "E6", "F6", "F5", "P", "F5", "P", "C6", "AS5", "A5", "C6", "F6", "P", "F6", "P", "G6", "FS6", "G6", "G5", "P", "G5", "P", "G6", "F6", "E6", "D6", "C6", "P", "C6", "P", "D6", "E6", "F6", "E6", "D6", "C6", "D6", "C6", "AS5", "A5", "AS5", "A5", "G5", "F5", "G5", "F5", "E5", "D5", "C5", "D5", "E5", "F5", "G5", "AS5", "A5", "G5", "A5", "F5", "P", "F5")

NOTE_DURATION = 0.150           # The time (in seconds) to play each note for. Change this to make the song play faster or slower


# Set the volume of the speaker output
set_volume(0.2)

# Clear all layers first
display.set_layer(0)
display.set_pen(BLACK)
display.clear()
display.set_layer(1)
display.set_pen(BLACK)
display.clear()

# Set the layer we're going to be drawing to.
display.set_layer(0)

# Set the background colour
display.set_pen(BG)
display.clear()

# Draw the drop shadow
display.set_pen(BLACK)
display.text("Press X\nto stop playback", 78, 78, WIDTH, 4)

# Draw the main text
display.set_pen(WHITE)
display.text("Press X\nto stop playback", 75, 75, WIDTH, 4)

# Screen update!
display.update()

# Play the song
for i in range(len(SONG)):
    if SONG[i] == "P":
        # This is a "pause" note, so stop the motors
        play_silence()
    else:
        # Get the frequency of the note and play it
        play_tone(TONES[SONG[i]])

    time.sleep(NOTE_DURATION)

    if button_x.value() == 0:
        stop_playing()
        break

stop_playing()

# Clear the screen
display.set_pen(BG)
display.clear()

# Draw the drop shadow
display.set_pen(BLACK)
display.text("The\nEnd", 128, 93, WIDTH, 4)

# Draw the main text
display.set_pen(WHITE)
display.text("The\nEnd", 125, 90, WIDTH, 4)

# Screen update!
display.update()

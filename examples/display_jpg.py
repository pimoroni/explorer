from pimoroni_explorer import display
import jpegdec

# Create a new JPEG decoder for our PicoGraphics
j = jpegdec.JPEG(display)

# Open the JPEG file
j.open_file("backgroundforscreen.jpg")

# Decode the JPEG
j.decode(0, 0, jpegdec.JPEG_SCALE_FULL, dither=True)

# Display the result
display.update()

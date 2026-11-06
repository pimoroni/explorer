import _input
import machine


class Button:
    def __init__(self, name, pin_name):
        self.name = name
        self.home_pin = getattr(machine.Pin.board, pin_name)
        self.pin = self.home_pin

    @property
    def held(self):
        return self.pin in _input.held

    @property
    def pressed(self):
        return self.pin in _input.pressed

    @property
    def released(self):
        return self.pin in _input.released

    def __repr__(self):
        return f"<Button {self.name}>"


button_a = Button("A", "BUTTON_A")
button_b = Button("B", "BUTTON_B")
button_c = Button("C", "BUTTON_C")
button_x = Button("X", "BUTTON_X")
button_y = Button("Y", "BUTTON_Y")
button_z = Button("Z", "BUTTON_Z")
button_user = Button("USER", "BUTTON_HOME")

buttons = (button_a, button_b, button_c, button_x, button_y, button_z, button_user)

SELECT = button_a
BACK = button_b
UP = button_x
DOWN = button_y
HOME = button_user

OPPOSITES = ((button_a, button_z), (button_b, button_y), (button_c, button_x))


def rotate_buttons(upside_down):
    for button, opposite in OPPOSITES:
        if upside_down:
            button.pin, opposite.pin = opposite.home_pin, button.home_pin
        else:
            button.pin, opposite.pin = button.home_pin, opposite.home_pin


def _matching(pins):
    return tuple(button for button in buttons if button.pin in pins)


def held():
    return _matching(_input.held)


def pressed():
    return _matching(_input.pressed)


def released():
    return _matching(_input.released)

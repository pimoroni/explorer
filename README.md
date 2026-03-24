# Explorer <!-- omit in toc -->

This repository is home to the Explorer MicroPython firmware and examples.

Explorer is a MicroPython-powered electronic adventure playground for physical computing, built around the RP2350B.

Grab yours at https://shop.pimoroni.com/products/explorer

- [Introduction](#introduction)
- [Download MicroPython for Explorer](#download-micropython-for-explorer)
- [Flashing The Firmware](#flashing-the-firmware)
- [Examples](#examples)
- [Documentation](#documentation)

# Introduction

Explorer comes pre-flashed with MicroPython, our own custom drivers/libraries and a range of examples to get you started. MicroPython support for the RP2350B is currently a work-in-progress, so you should be prepared to update as we make fixes and improvements!

# Download MicroPython for Explorer

To upgrade, grab the latest release from https://github.com/pimoroni/explorer/releases/latest

There are two choices of firmware:

* explorer-vX.X.X-micropython-with-filesystem.uf2 :warning:  (recommended) - A full update package including examples and the explorer library
* explorer-vX.X.X-micropython.uf2 - a firmware-only update, that will leave your filesystem alone!

:warning: If you flash the `with-filesystem` version, the contents of your Explorer board will be erased- so make sure to back up your own code first. Alternatively you can flash the firmware-only build and manually copy the files in [examples/lib](examples/lib)

# Flashing The Firmware

1. Connect Explorer to your computer with a USB Type-C cable
2. Put your Explorer into bootloader mode by holding down "BOOT", the second button from the left when holding Explorer with the screen facing away from you. Keep holding "BOOT" and press "RESET", the button next to "BOOT".
3. Drag and drop your chosen `.uf2` file onto the `RP2350` drive that appears.
4. Your board should reset and, if you used the `with-filesystem` build, should display a menu of examples.

# Examples

We've tried to cover all the bases with some simple examples to get you started. See [examples/README.md](examples/README.md) for more information.

# Documentation

To help you get started we've created a function reference. See [docs/reference.md](docs/reference.md)

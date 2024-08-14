# cmake file for the Pimoroni PGA2350
set(PICO_BOARD "explorer")
set(PICO_PLATFORM "rp2350-arm-s")
set(PICO_NUM_GPIOS 48)

# Make sure we find pga2350.h (PICO_BOARD) in the current dir
set(PICO_BOARD_HEADER_DIRS ${CMAKE_CURRENT_LIST_DIR})

# Board specific version of the frozen manifest
set(MICROPY_FROZEN_MANIFEST ${MICROPY_BOARD_DIR}/manifest.py)

# If USER_C_MODULES or MicroPython customisations use malloc then
# there needs to be some RAM reserved for the C heap
set(MICROPY_C_HEAP_SIZE 4096)
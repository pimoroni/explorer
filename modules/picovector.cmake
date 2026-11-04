if(NOT DEFINED PIMORONI_PICO_PATH)
set(PIMORONI_PICO_PATH ../pimoroni-pico)
endif()
include(${CMAKE_CURRENT_LIST_DIR}/../pimoroni_pico_import.cmake)

include_directories(${PIMORONI_PICO_PATH}/micropython)

list(APPEND CMAKE_MODULE_PATH "${PIMORONI_PICO_PATH}/micropython")
list(APPEND CMAKE_MODULE_PATH "${PIMORONI_PICO_PATH}/micropython/modules")

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}")

set(CMAKE_C_STANDARD 17)
set(CMAKE_CXX_STANDARD 17)

set(PV_DUAL_CORE ON)
find_package(PICOVECTOR_MICROPYTHON CONFIG REQUIRED)

include(c/input/micropython)
include(c/st7789/micropython)

include(pimoroni_i2c/micropython)

include(micropython-common-breakouts)

include(adcfft/micropython)

include(pwm/micropython)
include(servo/micropython)
include(encoder/micropython)
include(motor/micropython)

include(plasma/micropython)

include(micropython-common-ulab)
enable_ulab()

include(cppmem/micropython)

target_link_libraries(usermod INTERFACE hardware_powman)

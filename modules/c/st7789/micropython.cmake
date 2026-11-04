set(DRIVER_NAME st7789)
add_library(${DRIVER_NAME} INTERFACE)

target_sources(st7789 INTERFACE
  ${CMAKE_CURRENT_LIST_DIR}/st7789_bindings.c
  ${CMAKE_CURRENT_LIST_DIR}/st7789_bindings.cpp
  ${CMAKE_CURRENT_LIST_DIR}/st7789.cpp
)

pico_generate_pio_header(st7789 ${CMAKE_CURRENT_LIST_DIR}/st7789_parallel.pio)

target_include_directories(st7789 INTERFACE ${CMAKE_CURRENT_LIST_DIR})

# Pull in pico libraries that we need
target_link_libraries(st7789 INTERFACE pico_stdlib hardware_pwm hardware_pio hardware_dma)

target_link_libraries(usermod INTERFACE st7789)
#include "pico/stdlib.h"

static const uint BUTTON_PINS[] = {16, 15, 14, 17, 18, 19, 22};
static const uint BUTTON_COUNT = sizeof(BUTTON_PINS) / sizeof(BUTTON_PINS[0]);
static const uint BUTTON_USER_PIN = 22;
static const uint32_t DEBOUNCE_MS = 30;

extern "C" {
  #include "py/runtime.h"
  #include "py/mphal.h"

  #include "machine_pin.h"

  mp_obj_t ticks;

  uint8_t explorer_buttons;
  uint8_t explorer_changed_buttons;
  mp_uint_t explorer_ticks;
  mp_uint_t explorer_last_ticks;

  static bool buttons_initialised = false;
  static mp_uint_t button_changed_at[BUTTON_COUNT];

  static void init_buttons(void) {
    for(uint i = 0; i < BUTTON_COUNT; i++) {
      gpio_init(BUTTON_PINS[i]);
      gpio_set_dir(BUTTON_PINS[i], GPIO_IN);
      if(BUTTON_PINS[i] != BUTTON_USER_PIN) {
        gpio_pull_up(BUTTON_PINS[i]);
      }
    }
    sleep_us(100);
    buttons_initialised = true;
  }

  void input_attr(mp_obj_t self_in, qstr attr, mp_obj_t *dest) {
    (void)self_in;

    if(attr == MP_QSTR_ticks && dest[0] == MP_OBJ_NULL) {
      dest[0] = mp_obj_new_int_from_ll(explorer_ticks);
      return;
    }

    if(attr == MP_QSTR_ticks_delta && dest[0] == MP_OBJ_NULL) {
      dest[0] = mp_obj_new_int_from_ll(explorer_ticks - explorer_last_ticks);
      return;
    }

    if((attr == MP_QSTR_held || attr == MP_QSTR_pressed || attr == MP_QSTR_released || attr == MP_QSTR_changed) && dest[0] == MP_OBJ_NULL) {
      mp_obj_t t_items[BUTTON_COUNT];
      uint8_t buttons = 0;

      switch(attr) {
        case MP_QSTR_held:
          buttons = explorer_buttons;
          break;
        case MP_QSTR_pressed:
          buttons = explorer_buttons & explorer_changed_buttons;
          break;
        case MP_QSTR_released:
          buttons = ~explorer_buttons & explorer_changed_buttons;
          break;
        case MP_QSTR_changed:
          buttons = explorer_changed_buttons;
          break;
        default:
          break;
      }

      int n = 0;
      for(uint i = 0; i < BUTTON_COUNT; i++) {
        if(buttons & (1 << i)) {
          t_items[n] = MP_OBJ_FROM_PTR(machine_pin_find(MP_ROM_INT(BUTTON_PINS[i])));
          n++;
        }
      }
      dest[0] = mp_obj_new_tuple(n, t_items);
      return;
    }

    dest[1] = MP_OBJ_SENTINEL;
  }

  mp_obj_t mpy_binding_poll(void) {
    if(!buttons_initialised) {
      init_buttons();
    }

    mp_uint_t now = mp_hal_ticks_ms();
    uint8_t buttons = explorer_buttons;
    for(uint i = 0; i < BUTTON_COUNT; i++) {
      uint8_t bit = 1 << i;
      uint8_t level = gpio_get(BUTTON_PINS[i]) ? 0 : bit;
      if(level != (buttons & bit) && now - button_changed_at[i] >= DEBOUNCE_MS) {
        buttons ^= bit;
        button_changed_at[i] = now;
      }
    }

    explorer_changed_buttons = buttons ^ explorer_buttons;
    explorer_buttons = buttons;
    explorer_last_ticks = explorer_ticks;
    explorer_ticks = now;

    ticks = mp_obj_new_int_from_ll(explorer_ticks);
    return mp_const_none;
  }
}

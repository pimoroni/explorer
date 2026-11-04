#include "st7789.hpp"

// MicroPython's cooperative event pump (services USB, the scheduler, and pending
// exceptions). Declared with C linkage rather than including py/runtime.h, which
// isn't C++-safe: its declarations would get C++ linkage and fail to link. st7789
// needs nothing else from MicroPython.
extern "C" void mp_event_handle_nowait(void);

// picovector's framebuffer fence hook (see image.hpp): declared here rather
// than included, so this driver stays free of the 2D library's headers.
namespace picovector { extern void (*pv_fb_fence)(void); }

namespace pimoroni {

  // RGB565: picovector draws straight into 16-bit pixels (the format is a
  // platform detail - see RGB565 in picovector's image.hpp), which halves the
  // framebuffer to 150 KB and makes the scan-out below a byte swap and rotate.
  uint16_t __attribute__((section(".uninitialized_data"))) __attribute__ ((aligned (4))) framebuffer[320 * 240];
  uint16_t __attribute__((section(".uninitialized_data"))) __attribute__ ((aligned (4))) linebuffer[240 * 4];

  enum MADCTL : uint8_t {
    ROW_ORDER   = 0b10000000,
    COL_ORDER   = 0b01000000,
    SWAP_XY     = 0b00100000,  // AKA "MV"
    SCAN_ORDER  = 0b00010000,
    RGB_BGR     = 0b00001000,
    HORIZ_ORDER = 0b00000100
  };

  enum reg {
    SWRESET   = 0x01,
    TEOFF     = 0x34,
    TEON      = 0x35,
    STE       = 0x44,
    MADCTL    = 0x36,
    COLMOD    = 0x3A,
    RAMCTRL   = 0xB0,
    RGBCTRL   = 0xB1,
    GCTRL     = 0xB7,
    VCOMS     = 0xBB,
    LCMCTRL   = 0xC0,
    VDVVRHEN  = 0xC2,
    VRHS      = 0xC3,
    VDVS      = 0xC4,
    FRCTRL2   = 0xC6,
    PWCTRL1   = 0xD0,
    GATESEL   = 0xD6,
    PORCTRL   = 0xB2,
    GMCTRP1   = 0xE0,
    GMCTRN1   = 0xE1,
    INVOFF    = 0x20,
    SLPIN     = 0x10,
    SLPOUT    = 0x11,
    DISPON    = 0x29,
    GAMSET    = 0x26,
    DISPOFF   = 0x28,
    RAMWR     = 0x2C,
    INVON     = 0x21,
    CASET     = 0x2A,
    RASET     = 0x2B,
    PWMFRSEL  = 0xCC
  };

  void ST7789::init() {
    gpio_set_function(dc, GPIO_FUNC_SIO);
    gpio_set_dir(dc, GPIO_OUT);

    gpio_set_function(cs, GPIO_FUNC_SIO);
    gpio_set_dir(cs, GPIO_OUT);

    // if a backlight pin is provided then set it up for
    // pwm control
    pwm_config cfg = pwm_get_default_config();
    pwm_set_wrap(pwm_gpio_to_slice_num(bl), 65535);
    pwm_init(pwm_gpio_to_slice_num(bl), &cfg, true);
    gpio_set_function(bl, GPIO_FUNC_PWM);
    set_backlight(0); // Turn backlight off initially to avoid nasty surprises

    command(reg::SWRESET);

    sleep_ms(150);

    // Common init
    command(reg::COLMOD,    1, "\x05");  // 16 bits per pixel

    // both started as 0x0c 0x0c
    command(reg::PORCTRL, 5, "\x0c\x0c\x00\x33\x33");
    //command(reg::RGBCTRL, 3, "\x40\x02\x14");
    command(reg::LCMCTRL, 1, "\x2c");
    command(reg::VDVVRHEN, 1, "\x01");
    command(reg::VRHS, 1, "\x12");
    command(reg::VDVS, 1, "\x20");
    command(reg::PWCTRL1, 2, "\xa4\xa1");
    command(reg::FRCTRL2, 1, "\x0f");

    // As noted in https://github.com/pimoroni/pimoroni-pico/issues/1040
    // this is required to avoid a weird light grey banding issue with low brightness green.
    // The banding is not visible without tweaking gamma settings (GMCTRP1 & GMCTRN1) but
    // it makes sense to fix it anyway.
    command(reg::RAMCTRL, 2, "\x00\xc0");

    // 320 x 240
    command(reg::GCTRL, 1, "\x35");
    command(reg::VCOMS, 1, "\x1f");
    command(reg::GMCTRP1, 14, "\xD0\x08\x11\x08\x0C\x15\x39\x33\x50\x36\x13\x14\x29\x2D");
    command(reg::GMCTRN1, 14, "\xD0\x08\x10\x08\x06\x06\x39\x44\x51\x0B\x16\x14\x2F\x31");

    command(reg::INVON);   // set inversion mode
    command(reg::SLPOUT);  // leave sleep mode

    sleep_ms(100);

    uint16_t caset[2] = {0, 239};
    uint16_t raset[2] = {0, 319};

    // Byte swap the 16bit rows/cols values
    caset[0] = __builtin_bswap16(caset[0]);
    caset[1] = __builtin_bswap16(caset[1]);
    raset[0] = __builtin_bswap16(raset[0]);
    raset[1] = __builtin_bswap16(raset[1]);

    command(reg::CASET,  4, (char *)caset);
    command(reg::RASET,  4, (char *)raset);
    write_madctl();

    // Set up the screen for a display update
    uint8_t cmd = reg::RAMWR;
    gpio_put(dc, 0); // command mode
    gpio_put(cs, 0);
    write_blocking(&cmd, 1);
    gpio_put(dc, 1); // data mode

    // Temporarily reconfigure the DMA with no read increment so we can
    // clock out just one zero (no need to memset) to clear the whole display.
    linebuffer[0] = 0;
    configure_dma(false);
    write_blocking((uint8_t *)linebuffer, fullres_width * fullres_height * sizeof(uint16_t)); // Clear display to black
    configure_dma(true);

    command(reg::TEON, 1, "\x00");  // enable frame sync signal
    command(reg::STE, 2, "\x00\x00");
    command(reg::DISPON);  // turn display on
    set_backlight(230); // Turn backlight on now surprises have passed, 180 = about half perceptual brightness
  }

  uint16_t *ST7789::get_framebuffer() {
    return framebuffer;
  }

  static inline volatile void pio_sm_block_until_stalled(PIO pio, uint sm) {
    uint32_t sm_stall_mask = 1u << (sm + PIO_FDEBUG_TXSTALL_LSB);
    pio->fdebug = sm_stall_mask;
    while (!(pio->fdebug & sm_stall_mask))
        ;
  }

  inline void ST7789::wait_for_dma(void) {
    dma_channel_wait_for_finish_blocking(st_dma);

    // Prevent a race between PIO and chip-select or data/command
    // What's up with pio_sm_is_exec_stalled?
    pio_sm_block_until_stalled(parallel_pio, parallel_sm);
  }

  void ST7789::write_blocking(const uint8_t *src, size_t len) {
    dma_channel_set_trans_count(st_dma, len, false);
    dma_channel_set_read_addr(st_dma, src, true);
    wait_for_dma();
  }

  void ST7789::start_dma(const uint8_t *src, size_t len) {
    dma_channel_set_trans_count(st_dma, len, false);
    dma_channel_set_read_addr(st_dma, src, true);
  }

  void ST7789::command(uint8_t command, size_t len, const char *data) {
    // A command can arrive while an asynchronous frame is still streaming
    // (badge.poll()'s tilt auto-rotate lands right after update() returns).
    // Never inject bytes mid-frame, and leave stream mode first: the linear
    // path has the DMA reading 16-bit framebuffer words at PULL_THRESH 16, so
    // write_blocking would strobe garbage with DC low and derange the panel.
    if (async_enabled) {
      wait_for_stream();
      if (stream_mode) {
        wait_for_dma();
        set_pull_threshold(8);
        configure_dma(true);
        stream_mode = false;
      }
    }
    wait_for_dma();

    gpio_put(dc, 0); // command mode

    gpio_put(cs, 0);

    write_blocking(&command, 1);
    if(data) {
      gpio_put(dc, 1); // data mode
      write_blocking((const uint8_t*)data, len);
    }

    gpio_put(cs, 1);
  }

  // ---- asynchronous updates --------------------------------------------------
  // update() converts and sends column 0, then each DMA-complete interrupt
  // converts the next column into the idle linebuffer half and restarts the
  // DMA: the CPU pays ~4 us per column (the 565 framebuffer makes conversion a
  // byte-swap) and the frame streams out behind whatever runs next. Drawing is
  // fenced: picovector calls wait_for_stream() before the first framebuffer
  // write (pv_fb_fence, installed below), so user code computes freely and
  // stalls only if it draws before the panel has the frame.
  extern ST7789 *display_for_isr;
  ST7789 *display_for_isr = nullptr;

  static void __not_in_flash_func(st7789_dma_isr)() {
    if (display_for_isr) display_for_isr->stream_isr();
  }

  static void st7789_fb_fence() {
    if (display_for_isr) {
      display_for_isr->wait_for_stream();
      display_for_isr->apply_pending_clear();
    }
  }

  // Convert one framebuffer column into `dst` (rotated, panel byte order).
  void __not_in_flash_func(ST7789::convert_column)(uint16_t *dst, int x, bool fullres) {
    if (fullres) {
      for (int y = 0; y < fullres_height; y++)
        dst[y] = __builtin_bswap16(framebuffer[y * fullres_width + x]);
    } else {
      for (int y = 0; y < height; y++) {
        uint16_t pixel = __builtin_bswap16(framebuffer[y * width + x]);
        uint32_t doubled = pixel | ((uint32_t)pixel << 16);
        ((uint32_t *)dst)[y] = doubled;
        ((uint32_t *)dst)[height + y] = doubled;
      }
    }
  }

  // One DMA has just finished; stream_col is the next BATCH to send, and its
  // pixels are already converted in stream_a (one batch is always prepared
  // ahead, so the bus restarts within a couple of microseconds and the next
  // conversion happens while it drains). Full-res batches two columns per
  // interrupt - a linebuffer half holds exactly two - halving the interrupt
  // load on whatever the CPU is doing meanwhile; lores columns are already
  // double-width, one per half.
  void __not_in_flash_func(ST7789::stream_isr)() {
    dma_irqn_acknowledge_channel(1, st_dma);
    const int batch = stream_fullres ? 2 : 1;
    const int cols = stream_fullres ? fullres_width : width;
    if (stream_col >= cols) {
      dma_irqn_set_channel_enabled(1, st_dma, false);
      streaming = false;
      return;
    }
    const int sending = cols - stream_col < batch ? cols - stream_col : batch;
    dma_channel_set_trans_count(st_dma, stream_fullres ? fullres_height * 2 * sending : fullres_height * 4, false);
    dma_channel_set_read_addr(st_dma, stream_a, true);
    uint16_t *t = stream_a; stream_a = stream_b; stream_b = t;
    stream_col = stream_col + sending;
    for (int k = 0; k < batch && stream_col + k < cols; k++)
      convert_column(stream_a + (stream_fullres ? fullres_height * k : 0), stream_col + k, stream_fullres);
  }

  // The panel accepts either scan orientation. The synchronous path writes
  // column-major in the panel's native (portrait) order so vsync can chase the
  // refresh; the asynchronous full-res path flips MADCTL's SWAP_XY so the
  // row-major framebuffer streams out as ONE linear DMA with no CPU at all.
  // Sent before every RAMWR rather than only on change: a KeyboardInterrupt
  // can longjmp out of any wait (mp_event_handle_nowait), so a cached "what
  // the panel is set to" can lie across a soft reset. Re-sending is a few
  // microseconds and makes every frame self-healing.
  void ST7789::set_wire_landscape(bool landscape) {
    wire_landscape = landscape;
    uint8_t madctl;
    uint16_t caset[2], raset[2];
    if (landscape) {
      madctl = MADCTL::COL_ORDER | MADCTL::SWAP_XY;
      if (rotate_180) madctl ^= MADCTL::ROW_ORDER | MADCTL::COL_ORDER | MADCTL::SCAN_ORDER;
      caset[0] = 0; caset[1] = 319;
      raset[0] = 0; raset[1] = 239;
    } else {
      madctl = MADCTL::COL_ORDER;
      if (rotate_180) madctl ^= MADCTL::ROW_ORDER | MADCTL::COL_ORDER | MADCTL::SCAN_ORDER;
      caset[0] = 0; caset[1] = 239;
      raset[0] = 0; raset[1] = 319;
    }
    for (int i = 0; i < 2; i++) { caset[i] = __builtin_bswap16(caset[i]); raset[i] = __builtin_bswap16(raset[i]); }
    command(reg::CASET, 4, (char *)caset);
    command(reg::RASET, 4, (char *)raset);
    command(reg::MADCTL, 1, (char *)&madctl);
  }

  // The SM's autopull threshold: 8 for byte-wise commands and column streaming,
  // 16 for the linear framebuffer stream (a halfword FIFO write replicates, and
  // the left shift then sends the high byte first - exactly the panel's order).
  void ST7789::set_pull_threshold(uint8_t bits) {
    pio_sm_block_until_stalled(parallel_pio, parallel_sm);
    // The SM must be halted for the rest. Restart leaves the OSR empty, so
    // the first OUT after re-enable autopulls fresh data; an extra OUT here
    // would stall and then swallow the next word (the frame's first pixel,
    // or the first command byte).
    pio_sm_set_enabled(parallel_pio, parallel_sm, false);
    hw_write_masked(&parallel_pio->sm[parallel_sm].shiftctrl,
                    (uint32_t)(bits & 0x1f) << PIO_SM0_SHIFTCTRL_PULL_THRESH_LSB,
                    PIO_SM0_SHIFTCTRL_PULL_THRESH_BITS);
    pio_sm_restart(parallel_pio, parallel_sm);
    pio_sm_set_enabled(parallel_pio, parallel_sm, true);
  }

  void ST7789::apply_pending_clear() {
    if (!clear_pending) return;
    clear_pending = false;
    // the whole current-mode frame, as doubled 16-bit stores
    const uint32_t d = (uint32_t)clear_rgb565 | ((uint32_t)clear_rgb565 << 16);
    uint32_t *p = (uint32_t *)framebuffer;
    size_t words = (size_t)(fullres_mode ? fullres_width * fullres_height : width * height) / 2;
    while (words--) *p++ = d;
  }

  void ST7789::deferred_clear(uint8_t r, uint8_t g, uint8_t b) {
    clear_rgb565 = (uint16_t)(((r & 0xf8) << 8) | ((g & 0xfc) << 3) | (b >> 3));
    clear_pending = true;
    if (!async_enabled || !streaming) apply_pending_clear();
  }

  void ST7789::wait_for_stream() {
    while (streaming) {
      mp_event_handle_nowait();
    }
  }

  void ST7789::set_async(bool enabled) {
    wait_for_stream();
    async_enabled = enabled;
    display_for_isr = this;
    if (enabled) {
      irq_set_exclusive_handler(DMA_IRQ_1, st7789_dma_isr);
      irq_set_enabled(DMA_IRQ_1, true);
      picovector::pv_fb_fence = st7789_fb_fence;
    } else {
      dma_irqn_set_channel_enabled(1, st_dma, false);
      picovector::pv_fb_fence = nullptr;
    }
  }

  void ST7789::update() {
    // Determine clock divider
    const uint32_t sys_clk_hz = clock_get_hz(clk_sys);

    if (sys_clk_hz != startup_hz) {
      startup_hz = sys_clk_hz;
      pio_sm_set_clkdiv(parallel_pio, parallel_sm, fmax(1.0f, float(sys_clk_hz) / max_pio_clk));
    }

    wait_for_stream();
    wait_for_dma();
    // back to byte-wise commands, and the wire order this update writes in
    if (stream_mode) {
      set_pull_threshold(8);
      configure_dma(true);
      stream_mode = false;
    }
    set_wire_landscape(false);

    uint8_t cmd = reg::RAMWR;
    gpio_put(dc, 0); // command mode
    gpio_put(cs, 0);
    write_blocking(&cmd, 1);
    gpio_put(dc, 1); // data mode

    // Take an "a" and a "b" pointer into the linebuffer, we will swap between
    // these, converting pixels into one while the other is DMA'd to the screen.
    uint16_t *buf_a = linebuffer;
    uint16_t *buf_b = linebuffer + 240 * 2;

    if (async_enabled) {
      // Column walk in the panel's native scan order, so the frame chases
      // the refresh instead of tearing diagonally: send the first batch now,
      // the DMA interrupt walks the rest.
      stream_fullres = fullres_mode;
      stream_a = buf_a;
      stream_b = buf_b;
      stream_col = 0;
      streaming = true;
      convert_column(stream_a, 0, fullres_mode);
      if (fullres_mode) convert_column(stream_a + fullres_height, 1, true);
      dma_irqn_acknowledge_channel(1, st_dma);   // drop the stale RAMWR completion
      dma_irqn_set_channel_enabled(1, st_dma, true);
      stream_isr();                 // sends the first column, converts the next
      return;
    }

    // The copy from framebuffer to linebuffer also serves to rotate the image
    // 90 degrees to match the scan orientation and prevent diagonal tearing.
    if(fullres_mode) {
      for(int x = 0; x < fullres_width; x++) {
        for(int y = 0; y < fullres_height; y++) {
          // pixels are already RGB565: rotate and swap to the panel's byte order
          buf_a[y] = __builtin_bswap16(framebuffer[y * fullres_width + x]);
        }
        // Transfer a single full res (full 240 pixel height) column
        // In full-res we can "chase the beam" as it were, replacing pixels
        // behind the outgoing DMA transfer.
        wait_for_dma();
        start_dma((uint8_t *)buf_a, fullres_height * 2);
        std::swap(buf_a, buf_b);
      }
    } else {
      for(int x = 0; x < width; x++) {
        for(int y = 0; y < height; y++) {
          uint16_t pixel = __builtin_bswap16(framebuffer[y * width + x]);
          // Each source pixel is doubled across two columns (the 240px-tall
          // a/b halves of the linebuffer). Pack the horizontal pixel-doubling
          // into a single 32-bit store per column rather than two 16-bit stores.
          uint32_t doubled = pixel | ((uint32_t)pixel << 16);
          ((uint32_t *)buf_a)[y] = doubled;
          ((uint32_t *)buf_a)[height + y] = doubled;
        }
        wait_for_dma();
        start_dma((uint8_t *)buf_a, fullres_height * 2 * 2);
        std::swap(buf_a, buf_b);
      }
    }

    // Yeet the last column into the abyss and save a little time
    // wait_for_dma();
    // gpio_put(cs, 1);
  }

  bool ST7789::get_mode() {
    return this->fullres_mode;
  }

  void ST7789::set_mode(bool mode) {
    this->fullres_mode = mode;
  }

  void ST7789::set_backlight(uint8_t brightness) {
    // The backlight driver does not light below roughly 11% duty, and the
    // exact threshold varies between boards, so gamma correct the provided
    // 1-255 brightness value onto backlight_min-65535 for the pwm counter.
    // 0 is off.
    float gamma = 2.8;
    if(brightness == 0) {
      pwm_set_gpio_level(bl, 0);
      return;
    }
    float level = pow((float)(brightness) / 255.0f, gamma);
    uint16_t value = backlight_min + (uint16_t)(level * (65535.0f - backlight_min) + 0.5f);
    pwm_set_gpio_level(bl, value);
  }

  void ST7789::configure_dma(bool enable_read_increment) {
    dma_channel_config config = dma_channel_get_default_config(st_dma);
    channel_config_set_read_increment(&config, enable_read_increment);
    channel_config_set_transfer_data_size(&config, DMA_SIZE_8);
    channel_config_set_bswap(&config, false);
    channel_config_set_dreq(&config, pio_get_dreq(parallel_pio, parallel_sm, true));
    dma_channel_configure(st_dma, &config, &parallel_pio->txf[parallel_sm], NULL, 0, false);
  }

  void ST7789::set_max_pio_clock(uint32_t hz) {
    max_pio_clk = hz;
    startup_hz = 0;
  }

  void ST7789::write_madctl() {
    uint8_t madctl = MADCTL::COL_ORDER;
    if(rotate_180) {
      madctl ^= MADCTL::ROW_ORDER | MADCTL::COL_ORDER | MADCTL::SCAN_ORDER;
    }
    command(reg::MADCTL, 1, (char *)&madctl);
  }

  void ST7789::set_rotate_180(bool rotate) {
    if(rotate == rotate_180) return;
    rotate_180 = rotate;
    write_madctl();
    wire_landscape = false;   // write_madctl wrote portrait; async re-sends its own
  }

  uint8_t ST7789::set_framerate(uint8_t fps) {
    // FRCTRL2 (0xC6) RTNA[4:0] selects the normal-mode frame rate. The values
    // below are the approximate frame rates (Hz) for each RTNA setting with the
    // default porch configuration, taken from the ST7789 datasheet. The table
    // is indexed by RTNA value and runs from fastest (0x00) to slowest (0x1F).
    static const uint8_t rates[32] = {
      119, 111, 105,  99,  94,  90,  86,  82,
       78,  75,  72,  69,  67,  64,  62,  60,
       58,  57,  55,  53,  52,  50,  49,  48,
       46,  45,  44,  43,  42,  41,  40,  39,
    };

    // Pick the RTNA value whose frame rate is closest to the request.
    uint8_t best = 0;
    int best_err = 256;
    for(uint8_t i = 0; i < 32; i++) {
      int err = abs((int)rates[i] - (int)fps);
      if(err < best_err) {
        best_err = err;
        best = i;
      }
    }

    // Keep NLA[7:5] = 0 (dot inversion), matching the init-time default of 0x0f.
    uint8_t frctrl2 = best & 0x1f;
    command(reg::FRCTRL2, 1, (const char *)&frctrl2);

    return rates[best];
  }
}

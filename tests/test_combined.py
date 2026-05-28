# test_combined.py -- OLED + Buttons + Joystick + Encoder combined test
# ================================================================
# Shows all inputs on the OLED, using fast direct framebuffer writes.
#
# WHY THE LOOP IS STRUCTURED THIS WAY (don't change without reading):
# Software quadrature decoding of the EC11 needs A polled faster than
# one phase (~10-25ms at human rotation speed). An oled.show() over
# 1MHz I2C takes ~10-15ms, so if we redraw every iteration we sample A
# at random phases relative to B and miss/invert counts (the classic
# "rotates one way but counts ±1 randomly" symptom).
# Fix: the loop polls the encoder every ~1ms, but oled.show() only
# runs when a displayed value actually changed. While idle the encoder
# is sampled fast enough to be reliable; during real input the brief
# OLED windows fall in the encoder's "boring" phases (state 10 / 01)
# rather than the decision phases (11 / 00), so direction stays correct.
#
# Requires: adafruit_ssd1306.mpy in lib/, font5x8.bin at CIRCUITPY root
# Wiring: A0=JoyX, A1=JoyY, A2=JoyZ, A3=Buttons, D4=SDA, D5=SCL
#         D8=EncB, D9=EncA, D10=EncBtn
# Calibration: run test_joystick.py first to get CAL_X/Y/Z values

import board
import busio
import analogio
import digitalio
import time
import adafruit_ssd1306

# -- Setup -------------------------------------------------------------
# 1MHz I2C -- SSD1306 handles it (84 FPS raw transfer proven)
i2c = busio.I2C(scl=board.D5, sda=board.D4, frequency=1_000_000)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

joy_x = analogio.AnalogIn(board.A0)
joy_y = analogio.AnalogIn(board.A1)
joy_z = analogio.AnalogIn(board.A2)
btn_adc = analogio.AnalogIn(board.A3)

# Encoder pins with pull-ups
enc_a = digitalio.DigitalInOut(board.D9)
enc_a.direction = digitalio.Direction.INPUT
enc_a.pull = digitalio.Pull.UP

enc_b = digitalio.DigitalInOut(board.D8)
enc_b.direction = digitalio.Direction.INPUT
enc_b.pull = digitalio.Pull.UP

enc_btn = digitalio.DigitalInOut(board.D10)
enc_btn.direction = digitalio.Direction.INPUT
enc_btn.pull = digitalio.Pull.UP

# -- Load font ---------------------------------------------------------
try:
    with open("font5x8.bin", "rb") as f:
        raw = f.read()
    # font5x8.bin may have a 2-byte header (1282 bytes instead of 1280)
    # Skip header so character lookups are aligned correctly
    if len(raw) == 1282:
        FONT = raw[2:]
    else:
        FONT = raw
except OSError:
    print("ERROR: font5x8.bin not found on CIRCUITPY root!")
    raise SystemExit

# -- Fast framebuffer text ---------------------------------------------
buf = oled.buf
# oled.buf is the raw framebuffer (1024 bytes, no header)
# oled.buffer is the I2C buffer (1025 bytes, 0x40 header + data)
BUF_START = 0

def fast_text(text, x, page):
    """Write text directly to framebuffer -- 13x faster than oled.text()."""
    offset = BUF_START + page * 128 + x
    for ch in text:
        idx = ord(ch) * 5
        if offset + 5 > len(buf):
            break
        buf[offset] = FONT[idx]
        buf[offset + 1] = FONT[idx + 1]
        buf[offset + 2] = FONT[idx + 2]
        buf[offset + 3] = FONT[idx + 3]
        buf[offset + 4] = FONT[idx + 4]
        offset += 6  # 5px char + 1px gap

def clear_pages(start, end):
    """Clear a range of pages (8px rows each)."""
    begin = BUF_START + start * 128
    stop = min(BUF_START + (end + 1) * 128, len(buf))
    for i in range(begin, stop):
        buf[i] = 0

# -- Joystick calibration (from test_joystick.py) ---------------------
CAL_X = (489, 31979, 63522)
CAL_Y = (384, 31492, 63666)
CAL_Z = (438, 3490, 36000)
DEADZONE_PCT = 8

# -- Button thresholds (resistor ladder on A3, 2.2k pull-up) ---------
BUTTONS = [
    ("B1", 0,     2978),
    ("B2", 2979,  9626),
    ("B3", 9627,  16887),
    ("B4", 16888, 23523),
    ("B5", 23524, 31339),
    ("B6", 31340, 39005),
    ("B7", 39006, 45707),
    ("B8", 45708, 57525),
]
NO_PRESS = 57525

# -- Encoder state -----------------------------------------------------
enc_last_a = enc_a.value
enc_last_b = enc_b.value
enc_position = 0
enc_btn_pressed = False
enc_btn_count = 0
enc_btn_last_time = 0  # For debounce

# -- Helpers -----------------------------------------------------------

def read_joy(pin):
    """Single-read joystick axis."""
    return pin.value

def identify_button(val):
    for name, low, high in BUTTONS:
        if low <= val <= high:
            return name
    return "---" if val > NO_PRESS else "???"

def map_cal(raw, cal):
    """Map raw ADC to -99..+99 using (min, center, max) calibration."""
    cal_min, cal_center, cal_max = cal
    range_low = cal_center - cal_min
    range_high = cal_max - cal_center
    dz_low = int(range_low * DEADZONE_PCT / 100)
    dz_high = int(range_high * DEADZONE_PCT / 100)

    if cal_center - dz_low <= raw <= cal_center + dz_high:
        return 0
    if raw < cal_center - dz_low:
        effective = cal_center - dz_low - raw
        full_range = range_low - dz_low
        return max(-99, -int(effective * 99 / full_range)) if full_range > 0 else 0
    else:
        effective = raw - (cal_center + dz_high)
        full_range = range_high - dz_high
        return min(99, int(effective * 99 / full_range)) if full_range > 0 else 0

def num_to_str(n):
    """Format number as +XX or -XX with padding."""
    if n >= 0:
        s = "+" + str(n)
    else:
        s = str(n)
    while len(s) < 4:
        s = " " + s
    return s

def read_encoder():
    """Read quadrature encoder, 2x decoding on A edges.

    Direction rule (both edges of A counted):
      - When A changes, A == B means CW (+1), A != B means CCW (-1).
      - Works because for our EC11 phase, B settles ahead of A on each
        transition, so reading B at the instant A changes gives the
        rotation direction.
    Reliable only if this is called fast (~1ms) relative to one A phase.
    """
    global enc_last_a, enc_last_b, enc_position
    a = enc_a.value
    b = enc_b.value
    delta = 0
    if a != enc_last_a:
        delta = 1 if a == b else -1
        enc_position += delta
    enc_last_a = a
    enc_last_b = b
    return delta

# -- Debug print helper ------------------------------------------------
# Set to True to see REPL debug output
DEBUG = True

def debug(msg):
    if DEBUG:
        print(msg)

# -- Page layout -------------------------------------------------------
# 8 pages (0-7), each 8 pixels tall, total 64 pixels
#   Page 0 (rows 0-7):   Header
#   Page 1 (rows 8-15):  Separator
#   Page 2 (rows 16-23): Joystick XY
#   Page 3 (rows 24-31): Z rotation
#   Page 4 (rows 32-39): Encoder
#   Page 5 (rows 40-47): Direction
#   Page 6 (rows 48-55): (spare / encoder button)
#   Page 7 (rows 56-63): Button info
PG_HEAD = 0
PG_SEP  = 1
PG_XY   = 2
PG_Z    = 3
PG_ENC  = 4
PG_DIR  = 5
PG_EBTN = 6
PG_BTN  = 7

# -- Draw static header (once) ----------------------------------------
clear_pages(0, 7)
fast_text("DMX Controller", 0, PG_HEAD)
fast_text("----------------", 0, PG_SEP)
oled.show()

# -- Main loop ---------------------------------------------------------
print("Combined test (fast OLED) -- Ctrl+C to stop")

press_count = 0
last_btn = "---"

# "shown_*" mirrors what is currently drawn on the OLED. Each iteration
# we compare freshly-read inputs against this snapshot; if nothing
# changed there is no oled.show() call and the loop stays at ~1ms,
# which is what keeps encoder decoding reliable (see file header).
# Sentinel values (None / -1) guarantee a render on the first iteration.
shown_jx = shown_jy = shown_jz = None
shown_enc_pos = None
shown_enc_btn = None
shown_btn = None
shown_press_count = -1
shown_enc_btn_count = -1


try:
    while True:
        # --- Encoder FIRST, every loop, before anything slow -----------
        # Polling order matters: the encoder is the only input whose
        # accuracy depends on sample rate. Read it before the slower
        # joystick ADCs and well before any potential OLED redraw, so
        # that even on a "dirty" iteration A is sampled while the loop
        # has been running fast.
        enc_delta = read_encoder()
        enc_btn_state = not enc_btn.value  # Active low (pull-up to 3V3)

        if enc_delta != 0:
            debug(f"[ENC] delta={enc_delta:2d}  pos={enc_position:3d}")

        # Encoder button edge detection with debounce (50ms)
        now = time.monotonic()
        if enc_btn_state and not enc_btn_pressed and (now - enc_btn_last_time) > 0.05:
            enc_btn_count += 1
            enc_btn_pressed = True
            enc_btn_last_time = now
            debug(f"[BTN] PRESSED  count={enc_btn_count}")
        elif not enc_btn_state and enc_btn_pressed and (now - enc_btn_last_time) > 0.05:
            enc_btn_pressed = False
            enc_btn_last_time = now
            debug(f"[BTN] RELEASED count={enc_btn_count}")

        # --- Other inputs ----------------------------------------------
        btn = identify_button(btn_adc.value)
        if btn != "---" and btn != "???" and last_btn == "---":
            press_count += 1
        last_btn = btn

        jx = map_cal(read_joy(joy_x), CAL_X)
        jy = map_cal(read_joy(joy_y), CAL_Y)
        jz = map_cal(read_joy(joy_z), CAL_Z)

        # --- Redraw only if something visible changed ------------------
        # This is the key to the whole design: oled.show() is the
        # expensive operation (~10-15ms). Skipping it when no value
        # changed keeps the idle loop near 1ms and lets the encoder
        # be polled at a rate that fits within one A phase.
        dirty = (
            jx != shown_jx or jy != shown_jy or jz != shown_jz
            or enc_position != shown_enc_pos
            or enc_btn_state != shown_enc_btn
            or btn != shown_btn
            or press_count != shown_press_count
            or enc_btn_count != shown_enc_btn_count
        )

        if dirty:
            # Clear dynamic pages
            clear_pages(PG_XY, PG_BTN)

            # Joystick XY
            fast_text("X:" + num_to_str(jx) + " Y:" + num_to_str(jy), 0, PG_XY)

            # Z rotation with bar
            zabs = abs(jz) // 10
            if jz > 0:
                fast_text("Z: CW  " + "=" * zabs, 0, PG_Z)
            elif jz < 0:
                fast_text("Z: CCW " + "=" * zabs, 0, PG_Z)
            else:
                fast_text("Z: ---", 0, PG_Z)

            # Encoder position
            fast_text("Enc:" + str(enc_position), 0, PG_ENC)

            # Direction
            dx = "R" if jx > 15 else ("L" if jx < -15 else "-")
            dy = "U" if jy > 15 else ("D" if jy < -15 else "-")
            fast_text("Dir: " + dx + " " + dy, 0, PG_DIR)

            # Encoder button
            ebtn_str = "PUSH" if enc_btn_state else "----"
            fast_text("Ebtn:" + ebtn_str + " #" + str(enc_btn_count), 0, PG_EBTN)

            # Button
            fast_text("Btn:" + btn + " #" + str(press_count), 0, PG_BTN)

            oled.show()

            # Commit the rendered snapshot so the next iteration's
            # change-detection compares against what is actually on
            # the panel, not against the previous in-memory state.
            shown_jx, shown_jy, shown_jz = jx, jy, jz
            shown_enc_pos = enc_position
            shown_enc_btn = enc_btn_state
            shown_btn = btn
            shown_press_count = press_count
            shown_enc_btn_count = enc_btn_count

        # Minimum 1ms between polls. On an idle iteration the loop is
        # essentially this sleep + a handful of pin reads, which is the
        # same effective sampling rate as test_ec11.py.
        time.sleep(0.001)

except KeyboardInterrupt:
    clear_pages(0, 7)
    fast_text("Test done!", 0, 2)
    fast_text("Btn:" + str(press_count) + " Enc:" + str(enc_position), 0, 3)
    oled.show()
    print("\nDone. " + str(press_count) + " btn presses, encoder pos: " + str(enc_position))


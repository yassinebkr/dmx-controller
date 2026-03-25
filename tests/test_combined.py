# test_combined.py -- OLED + Buttons + Joystick combined test
# ============================================================
# Shows all inputs on the OLED in real-time using fast direct
# framebuffer writes (~40 FPS vs 3 FPS with oled.text()).
#
# Requires: adafruit_ssd1306.mpy in lib/, font5x8.bin at CIRCUITPY root
# Wiring: A0=JoyX, A1=JoyY, A2=JoyZ, A3=Buttons, D4=SDA, D5=SCL
# Calibration: run test_joystick.py first to get CAL_X/Y/Z values

import board
import busio
import analogio
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
# oled.buf has a 1-byte header (0x40 = I2C data command)
# Pixel data starts at buf[1], not buf[0]
BUF_START = 1

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
    for i in range(BUF_START + start * 128, BUF_START + (end + 1) * 128):
        buf[i] = 0

# -- Joystick calibration (from test_joystick.py) ---------------------
CAL_X = (489, 31979, 63522)
CAL_Y = (384, 31492, 63666)
CAL_Z = (438, 3490, 36000)
DEADZONE_PCT = 8

# -- Button thresholds (resistor ladder on A3) -------------------------
BUTTONS = [
    ("B1", 0,     3000),
    ("B2", 3000,  10000),
    ("B3", 10000, 20000),
    # ("B4", 20000, 25000),
    # ("B5", 25000, 33000),
    # ("B6", 33000, 40500),
    # ("B7", 40500, 47000),
    # ("B8", 47000, 55000),
]
NO_PRESS = 55000

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

# -- Draw static header (once) ----------------------------------------
clear_pages(0, 7)
fast_text("DMX Controller", 0, 0)
fast_text("----------------", 0, 1)
oled.show()

# -- Main loop ---------------------------------------------------------
print("Combined test (fast OLED) -- Ctrl+C to stop")

press_count = 0
last_btn = "---"

try:
    while True:
        # Read inputs
        btn = identify_button(btn_adc.value)
        if btn != "---" and btn != "???" and last_btn == "---":
            press_count += 1
        last_btn = btn

        jx = map_cal(read_joy(joy_x), CAL_X)
        jy = map_cal(read_joy(joy_y), CAL_Y)
        jz = map_cal(read_joy(joy_z), CAL_Z)

        # Clear only dynamic pages (2-6), keep header
        clear_pages(2, 6)

        # Joystick XY
        fast_text("X:" + num_to_str(jx) + " Y:" + num_to_str(jy), 0, 2)

        # Z rotation with bar
        zabs = abs(jz) // 10
        if jz > 0:
            fast_text("Z: CW  " + "=" * zabs, 0, 3)
        elif jz < 0:
            fast_text("Z: CCW " + "=" * zabs, 0, 3)
        else:
            fast_text("Z: ---", 0, 3)

        # Direction
        dx = "R" if jx > 15 else ("L" if jx < -15 else "-")
        dy = "U" if jy > 15 else ("D" if jy < -15 else "-")
        fast_text("Dir: " + dx + " " + dy, 0, 4)

        # Button
        fast_text("Btn:" + btn + " #" + str(press_count), 0, 5)

        oled.show()

except KeyboardInterrupt:
    clear_pages(0, 7)
    fast_text("Test done!", 0, 2)
    fast_text(str(press_count) + " presses", 0, 3)
    oled.show()
    print("\nDone. " + str(press_count) + " presses.")

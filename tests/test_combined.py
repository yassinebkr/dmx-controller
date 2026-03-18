# test_combined.py — OLED + Buttons + Joystick combined test
# Shows all inputs on the OLED in real-time
# Requires: adafruit_ssd1306.mpy + adafruit_framebuf.mpy in lib/
#           font5x8.bin at CIRCUITPY root
# Wiring: A0=JoyX, A1=JoyY, A2=JoyZ, A3=Buttons, D4=SDA, D5=SCL
#
# !! IMPORTANT: Run test_joystick.py first to get your calibration values,
# then paste them below in the CAL_X/Y/Z lines !!

import board
import busio
import analogio
import time
import adafruit_ssd1306

# --- Setup ---
i2c = busio.I2C(scl=board.D5, sda=board.D4)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

joy_x = analogio.AnalogIn(board.A0)
joy_y = analogio.AnalogIn(board.A1)
joy_z = analogio.AnalogIn(board.A2)
btn_adc = analogio.AnalogIn(board.A3)

# ==============================================================
# CALIBRATION VALUES — paste from test_joystick.py Phase 2 output
# Format: (min, center, max)
# ==============================================================
CAL_X = (400, 30000, 60000)    # <-- REPLACE with your values
CAL_Y = (400, 30000, 60000)    # <-- REPLACE with your values
CAL_Z = (400, 3000, 30000)     # <-- REPLACE with your values
DEADZONE_PCT = 8               # % of range treated as center

# --- Button config (3 wired for now) ---
BUTTONS = [
    {"name": "B1", "low": 0,     "high": 3000},
    {"name": "B2", "low": 3000,  "high": 10000},
    {"name": "B3", "low": 10000, "high": 20000},
    # Uncomment as you wire more buttons:
    # {"name": "B4", "low": 20000, "high": 25000},
    # {"name": "B5", "low": 25000, "high": 33000},
    # {"name": "B6", "low": 33000, "high": 40500},
    # {"name": "B7", "low": 40500, "high": 47000},
    # {"name": "B8", "low": 47000, "high": 55000},
]
NO_PRESS = 55000

# --- Helpers ---

def read_avg(adc_pin, n=5):
    total = 0
    for _ in range(n):
        total += adc_pin.value
        time.sleep(0.002)
    return total // n

def identify_button(val):
    for b in BUTTONS:
        if b["low"] <= val <= b["high"]:
            return b["name"]
    return "---" if val > NO_PRESS else "???"

def map_calibrated(raw, cal, deadzone_pct=DEADZONE_PCT):
    """Map raw ADC to -99..+99 using (min, center, max) calibration."""
    cal_min, cal_center, cal_max = cal
    range_low = cal_center - cal_min
    range_high = cal_max - cal_center
    dz_low = int(range_low * deadzone_pct / 100)
    dz_high = int(range_high * deadzone_pct / 100)

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

# --- Main loop ---
print("Combined test: OLED + Joystick + Buttons")
print("Ctrl+C to stop")

press_count = 0
last_btn = "---"

try:
    while True:
        # Read all inputs
        bval = read_avg(btn_adc)
        btn = identify_button(bval)

        jx = map_calibrated(read_avg(joy_x), CAL_X)
        jy = map_calibrated(read_avg(joy_y), CAL_Y)
        jz = map_calibrated(read_avg(joy_z), CAL_Z)

        if btn != "---" and btn != "???" and last_btn == "---":
            press_count += 1
        last_btn = btn

        # Update OLED
        oled.fill(0)
        oled.text("DMX Controller", 0, 0, 1)
        oled.text("----------------", 0, 9, 1)

        # Joystick mapped values
        oled.text("X:{:+3d} Y:{:+3d}".format(jx, jy), 0, 20, 1)

        # Z rotation with visual indicator
        zbar = "=" * (abs(jz) // 10)
        if jz > 0:
            oled.text("Z: CW  " + zbar, 0, 30, 1)
        elif jz < 0:
            oled.text("Z: CCW " + zbar, 0, 30, 1)
        else:
            oled.text("Z: ---", 0, 30, 1)

        # Direction
        dx = "R" if jx > 15 else ("L" if jx < -15 else "-")
        dy = "U" if jy > 15 else ("D" if jy < -15 else "-")
        oled.text("Dir: {} {}".format(dx, dy), 0, 42, 1)

        # Button
        oled.text("Btn:{} #{}".format(btn, press_count), 0, 54, 1)

        oled.show()
        time.sleep(0.06)

except KeyboardInterrupt:
    oled.fill(0)
    oled.text("Test done!", 0, 20, 1)
    oled.text("{} presses".format(press_count), 0, 32, 1)
    oled.show()
    print(f"\nDone. {press_count} presses.")

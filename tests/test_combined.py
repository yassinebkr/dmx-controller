# test_combined.py -- OLED + Buttons + Joystick combined test
# Shows all inputs on the OLED in real-time
# Requires: adafruit_ssd1306.mpy + adafruit_framebuf.mpy in lib/
#           font5x8.bin at CIRCUITPY root
# Wiring: A0=JoyX, A1=JoyY, A2=JoyZ, A3=Buttons, D4=SDA, D5=SCL
#
# Calibration: run test_joystick.py first to get your CAL_X/Y/Z values

import board
import busio
import analogio
import time
import adafruit_ssd1306

# -- Setup ---------------------------------------------------------
# 400kHz I2C -- SSD1306 supports up to 400kHz
# Default is 100kHz which makes oled.show() take ~100ms (= 10 FPS max)
# At 400kHz, oled.show() takes ~25ms (= ~40 FPS)
i2c = busio.I2C(scl=board.D5, sda=board.D4, frequency=400000)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

joy_x = analogio.AnalogIn(board.A0)
joy_y = analogio.AnalogIn(board.A1)
joy_z = analogio.AnalogIn(board.A2)
btn_adc = analogio.AnalogIn(board.A3)

# -- Joystick calibration (from test_joystick.py Phase 2) ----------
CAL_X = (489, 31979, 63522)    # calibrated 2026-03-18
CAL_Y = (384, 31492, 63666)    # calibrated 2026-03-18
CAL_Z = (438, 3490, 36000)     # calibrated 2026-03-18
DEADZONE_PCT = 8               # % of range treated as center

# -- Button thresholds (resistor ladder on A3) ---------------------
# 2k pull-up to 3.3V, buttons to GND through individual resistors
# CircuitPython ADC = 16-bit (0-65535)
BUTTONS = [
    ("B1", 0,     3000),     # 0 ohm
    ("B2", 3000,  10000),    # 220 ohm
    ("B3", 10000, 20000),    # 560 ohm
    # Uncomment as you wire more buttons:
    # ("B4", 20000, 25000),  # 1k ohm
    # ("B5", 25000, 33000),  # 1.5k ohm
    # ("B6", 33000, 40500),  # 2.7k ohm
    # ("B7", 40500, 47000),  # 3.9k ohm
    # ("B8", 47000, 55000),  # 6.8k ohm
]
NO_PRESS = 55000  # above this = no button pressed

# -- Helpers -------------------------------------------------------

def read_joy(pin):
    """Read joystick axis -- 2 samples, no delay (fast)."""
    return (pin.value + pin.value) >> 1

def read_btn():
    """Read button ADC -- single sample, fast."""
    return btn_adc.value

def identify_button(val):
    """Match ADC value to a button name using thresholds."""
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

# -- Main loop -----------------------------------------------------
# Target: ~30 FPS
# Loop time budget:
#   - Joystick reads (3 axes, 2 samples each): ~1ms
#   - Button read (3 samples, 1ms delay): ~3ms
#   - OLED fill + text + show (I2C transfer): ~20ms
#   - No extra sleep needed -- I2C is the natural frame limiter

print("Combined test: OLED + Joystick + Buttons")
print("Ctrl+C to stop")

press_count = 0
last_btn = "---"
frame = 0

# Static text -- draw once, then only update dynamic parts
oled.fill(0)
oled.text("DMX Controller", 0, 0, 1)
oled.text("----------------", 0, 9, 1)
oled.show()

try:
    while True:
        # Read button every cycle -- instant response
        btn = identify_button(read_btn())
        if btn != "---" and btn != "???" and last_btn == "---":
            press_count += 1
        last_btn = btn

        # Read joystick every cycle
        jx = map_cal(read_joy(joy_x), CAL_X)
        jy = map_cal(read_joy(joy_y), CAL_Y)
        jz = map_cal(read_joy(joy_z), CAL_Z)

        # Update OLED every 3rd cycle -- display is slow, inputs are fast
        frame += 1
        if frame >= 3:
            frame = 0

            oled.fill(0)
            oled.text("DMX Controller", 0, 0, 1)
            oled.text("----------------", 0, 9, 1)
            oled.text("X:{:+3d} Y:{:+3d}".format(jx, jy), 0, 20, 1)

            if jz > 0:
                oled.text("Z: CW  " + "=" * (abs(jz) // 10), 0, 30, 1)
            elif jz < 0:
                oled.text("Z: CCW " + "=" * (abs(jz) // 10), 0, 30, 1)
            else:
                oled.text("Z: ---", 0, 30, 1)

            dx = "R" if jx > 15 else ("L" if jx < -15 else "-")
            dy = "U" if jy > 15 else ("D" if jy < -15 else "-")
            oled.text("Dir: {} {}".format(dx, dy), 0, 42, 1)
            oled.text("Btn:{} #{}".format(btn, press_count), 0, 54, 1)
            oled.show()

except KeyboardInterrupt:
    oled.fill(0)
    oled.text("Test done!", 0, 20, 1)
    oled.text("{} presses".format(press_count), 0, 32, 1)
    oled.show()
    print("\nDone. " + str(press_count) + " presses.")

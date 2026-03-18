# test_combined.py — OLED + Buttons + Joystick combined test
# Shows all inputs on the OLED in real-time
# Requires: adafruit_ssd1306.mpy + adafruit_framebuf.mpy in lib/
#           font5x8.bin at CIRCUITPY root
# Wiring: A0=JoyX, A1=JoyY, A2=JoyZ, A3=Buttons, D4=SDA, D5=SCL

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

# --- Joystick config ---
# Adjust after running test_joystick.py Phase 1
CENTER_X = 32768
CENTER_Y = 32768
CENTER_Z = 32768
DEADZONE = 3000

def read_avg(adc_pin, n=5):
    """Read ADC with averaging."""
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

def map_axis(raw, center, deadzone=DEADZONE):
    """Map raw 16-bit ADC to -99..+99 with deadzone."""
    diff = raw - center
    if abs(diff) < deadzone:
        return 0
    if diff > 0:
        maxrange = 65535 - center - deadzone
        return min(99, int((diff - deadzone) / maxrange * 99)) if maxrange > 0 else 0
    else:
        maxrange = center - deadzone
        return max(-99, int((diff + deadzone) / maxrange * 99)) if maxrange > 0 else 0

# --- Visual helpers ---
def bar(value, width=20):
    """Draw a horizontal bar for -99..+99 range.
    Returns a string like: [====|     ] or [     |===]
    """
    mid = width // 2
    filled = int(abs(value) / 99 * mid)
    if value >= 0:
        left = " " * mid
        right = "=" * filled + " " * (mid - filled)
    else:
        left = " " * (mid - filled) + "=" * filled
        right = " " * mid
    return left + "|" + right

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

        jx = map_axis(read_avg(joy_x), CENTER_X)
        jy = map_axis(read_avg(joy_y), CENTER_Y)
        jz = map_axis(read_avg(joy_z), CENTER_Z)

        if btn != "---" and btn != "???" and last_btn == "---":
            press_count += 1
        last_btn = btn

        # Update OLED
        oled.fill(0)
        oled.text("DMX Controller", 0, 0, 1)
        oled.text("----------------", 0, 9, 1)

        # Joystick: show mapped values
        oled.text("X:{:+3d} Y:{:+3d} Z:{:+3d}".format(jx, jy, jz), 0, 20, 1)

        # Direction indicator
        dx = "R" if jx > 20 else ("L" if jx < -20 else "-")
        dy = "U" if jy > 20 else ("D" if jy < -20 else "-")
        dz = "+" if jz > 20 else ("-" if jz < -20 else "0")
        oled.text("Dir: {} {} Rot:{}".format(dx, dy, dz), 0, 32, 1)

        # Button
        oled.text("Btn: {}".format(btn), 0, 44, 1)
        oled.text("Presses: {}".format(press_count), 0, 54, 1)

        oled.show()

        # Serial output too
        print(f"Joy X:{jx:+3d} Y:{jy:+3d} Z:{jz:+3d} | Btn:{btn:>3s} | #{press_count}")

        time.sleep(0.06)

except KeyboardInterrupt:
    oled.fill(0)
    oled.text("Test done!", 0, 20, 1)
    oled.text("{} presses".format(press_count), 0, 32, 1)
    oled.show()
    print(f"\nDone. {press_count} presses.")

# test_combined.py — OLED + Buttons combined test
# Shows button presses on the OLED in real-time
# Requires: adafruit_ssd1306.mpy + adafruit_framebuf.mpy in CIRCUITPY/lib/
# Wiring: A3=buttons, D4=SDA, D5=SCL

import board
import busio
import analogio
import time
import adafruit_ssd1306

# --- Setup ---
i2c = busio.I2C(scl=board.D5, sda=board.D4)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
adc = analogio.AnalogIn(board.A3)

BUTTONS = [
    {"name": "B1 (0ohm)",   "low": 0,     "high": 3000},
    {"name": "B2 (220ohm)", "low": 3000,  "high": 10000},
    {"name": "B3 (560ohm)", "low": 10000, "high": 20000},
]
NO_PRESS = 50000

def read_avg(n=5):
    total = 0
    for _ in range(n):
        total += adc.value
        time.sleep(0.003)
    return total // n

def identify(val):
    for b in BUTTONS:
        if b["low"] <= val <= b["high"]:
            return b["name"]
    return None if val > NO_PRESS else "???"

# --- Main loop ---
print("Combined test — OLED + Buttons")
print("Ctrl+C to stop")

press_count = 0
last = None

try:
    while True:
        val = read_avg()
        volts = val * 3.3 / 65535
        btn = identify(val)

        if btn and btn != last:
            press_count += 1
        last = btn

        # Update OLED
        oled.fill(0)
        oled.text("DMX Controller", 0, 0, 1)
        oled.text("----------------", 0, 10, 1)

        if btn:
            oled.text("Button: " + btn, 0, 22, 1)
        else:
            oled.text("Button: ---", 0, 22, 1)

        oled.text("ADC: " + str(val), 0, 34, 1)
        oled.text("V:   " + "{:.2f}".format(volts), 0, 44, 1)
        oled.text("Count: " + str(press_count), 0, 54, 1)
        oled.show()

        time.sleep(0.08)

except KeyboardInterrupt:
    oled.fill(0)
    oled.text("Test done!", 0, 28, 1)
    oled.text(str(press_count) + " presses", 0, 40, 1)
    oled.show()
    print(f"Done. {press_count} button presses detected.")

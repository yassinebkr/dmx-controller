# test_oled.py — SSD1306 OLED test for XIAO RP2040
# Requires: adafruit_ssd1306.mpy + adafruit_framebuf.mpy in CIRCUITPY/lib/
# Wiring: SDA → D4, SCL → D5, VCC → 3.3V, GND → GND

import board
import busio
import time
import adafruit_ssd1306

# XIAO RP2040: D5 = SCL, D4 = SDA
i2c = busio.I2C(scl=board.D5, sda=board.D4)

# SSD1306 128x64 OLED — default I2C address 0x3C
# If yours is 0x3D, change the addr parameter
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

# --- Test 1: Fill entire screen white, then black ---
print("Test 1: Fill white")
oled.fill(1)
oled.show()
time.sleep(1)

print("Test 1: Fill black")
oled.fill(0)
oled.show()
time.sleep(0.5)

# --- Test 2: Display text ---
print("Test 2: Text display")
oled.fill(0)
oled.text("DMX Controller", 0, 0, 1)
oled.text("XIAO RP2040", 0, 12, 1)
oled.text("XBee S1", 0, 24, 1)
oled.text("----------------", 0, 36, 1)
oled.text("OLED OK!", 0, 50, 1)
oled.show()
time.sleep(2)

# --- Test 3: Draw some shapes ---
print("Test 3: Shapes")
oled.fill(0)

# Rectangle border
for x in range(128):
    oled.pixel(x, 0, 1)
    oled.pixel(x, 63, 1)
for y in range(64):
    oled.pixel(0, y, 1)
    oled.pixel(127, y, 1)

# Diagonal line
for i in range(64):
    oled.pixel(i * 2, i, 1)

oled.text("Shapes OK", 40, 28, 1)
oled.show()
time.sleep(2)

# --- Test 4: Scrolling counter ---
print("Test 4: Counter (Ctrl+C to stop)")
count = 0
try:
    while True:
        oled.fill(0)
        oled.text("Counter:", 0, 0, 1)
        oled.text(str(count), 0, 16, 1)
        oled.text("Press Ctrl+C", 0, 48, 1)
        oled.show()
        count += 1
        time.sleep(0.2)
except KeyboardInterrupt:
    oled.fill(0)
    oled.text("Test complete!", 0, 28, 1)
    oled.show()
    print("Done.")

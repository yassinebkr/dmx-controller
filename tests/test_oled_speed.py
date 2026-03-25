# test_oled_speed.py -- Find the OLED speed bottleneck
# ====================================================
# Runs 3 benchmarks to isolate what's slow:
#   1. Pure I2C transfer (show() only, no rendering)
#   2. Fill + show (framebuf clear + transfer)
#   3. Full render (text + show)
#
# At 400kHz I2C, 1024 bytes should transfer in ~23ms = ~43 FPS
# If we're getting 4 FPS, this test will show where the time goes.

import board
import busio
import time
import adafruit_ssd1306

# Try 400kHz and 1MHz to see if frequency actually changes speed
i2c = busio.I2C(scl=board.D5, sda=board.D4, frequency=400_000)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

def benchmark(name, func, iterations=50):
    """Run func N times and report FPS."""
    start = time.monotonic()
    for _ in range(iterations):
        func()
    elapsed = time.monotonic() - start
    fps = iterations / elapsed
    ms = (elapsed / iterations) * 1000
    print(name + ": " + str(round(fps, 1)) + " FPS (" + str(round(ms, 1)) + " ms/frame)")

print("=" * 40)
print("  OLED Speed Benchmark")
print("  I2C freq requested: 400kHz")
print("=" * 40)

# Test 1: pure show() -- just I2C transfer, no rendering
# This is the absolute speed ceiling
print("\n[1] Pure I2C transfer (show only)...")
oled.fill(0)
benchmark("show() only", oled.show)

# Test 2: fill + show -- clear buffer + transfer
print("\n[2] Fill + show...")
def fill_and_show():
    oled.fill(0)
    oled.show()
benchmark("fill+show", fill_and_show)

# Test 3: one line of text + show
print("\n[3] One text line + show...")
def text_and_show():
    oled.fill(0)
    oled.text("Hello World", 0, 0, 1)
    oled.show()
benchmark("1 text+show", text_and_show)

# Test 4: full screen text (7 lines) + show
print("\n[4] Full text (7 lines) + show...")
def full_text_and_show():
    oled.fill(0)
    oled.text("DMX Controller", 0, 0, 1)
    oled.text("----------------", 0, 9, 1)
    oled.text("X: +50 Y: -30", 0, 20, 1)
    oled.text("Z: CW  =====", 0, 30, 1)
    oled.text("Dir: R U", 0, 42, 1)
    oled.text("Btn:B1 #5", 0, 54, 1)
    oled.show()
benchmark("7 text+show", full_text_and_show)

# Test 5: try 1MHz I2C
print("\n[5] Retesting at 1MHz I2C...")
i2c.deinit()
i2c = busio.I2C(scl=board.D5, sda=board.D4, frequency=1_000_000)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
oled.fill(0)
benchmark("1MHz show()", oled.show)

def full_1mhz():
    oled.fill(0)
    oled.text("DMX Controller", 0, 0, 1)
    oled.text("----------------", 0, 9, 1)
    oled.text("X: +50 Y: -30", 0, 20, 1)
    oled.text("Z: CW  =====", 0, 30, 1)
    oled.text("Dir: R U", 0, 42, 1)
    oled.text("Btn:B1 #5", 0, 54, 1)
    oled.show()
benchmark("1MHz full", full_1mhz)

print("\nDone!")

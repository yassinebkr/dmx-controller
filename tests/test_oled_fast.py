# test_oled_fast.py -- Fast OLED rendering via direct framebuffer writes
# =====================================================================
# The adafruit_framebuf text() function renders pixel-by-pixel in Python
# which takes ~45ms per line. This approach writes font bytes directly
# to the SSD1306 buffer -- 5 bytes per character, no pixel loops.
#
# SSD1306 buffer layout: 8 pages × 128 columns
# Each byte = 8 vertical pixels (LSB = top)
# Page 0 = rows 0-7, Page 1 = rows 8-15, etc.
#
# Requires: font5x8.bin at CIRCUITPY root (same as before)
# Wiring: SDA=D4, SCL=D5

import board
import busio
import time
import adafruit_ssd1306

# 1MHz I2C -- SSD1306 handles it fine (benchmark proved 84 FPS)
i2c = busio.I2C(scl=board.D5, sda=board.D4, frequency=1_000_000)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

# -- Load 5x8 font from font5x8.bin ----------------------------------
# font5x8.bin: 256 characters × 5 bytes each = 1280 bytes
# Each character is 5 columns of 8-bit vertical bitmaps
try:
    with open("font5x8.bin", "rb") as f:
        FONT = f.read()
    print("Font loaded: " + str(len(FONT)) + " bytes")
except OSError:
    print("ERROR: font5x8.bin not found on CIRCUITPY root!")
    raise SystemExit

# -- Direct buffer access ---------------------------------------------
# adafruit_ssd1306 stores the framebuffer in oled.buf
# It's a bytearray of 1024 bytes (128 × 8 pages)
# Byte at index (page * 128 + col) controls 8 vertical pixels at that column
buf = oled.buf

def fast_text(text, x, page):
    """
    Write text directly to the framebuffer.
    x: pixel column (0-127)
    page: display page 0-7 (each page = 8 pixel rows)
    
    ~20x faster than oled.text() because we copy font bytes
    directly instead of setting pixels one at a time.
    """
    offset = page * 128 + x
    for ch in text:
        idx = ord(ch) * 5
        if offset + 5 > 1024:
            break  # don't overflow buffer
        buf[offset] = FONT[idx]
        buf[offset + 1] = FONT[idx + 1]
        buf[offset + 2] = FONT[idx + 2]
        buf[offset + 3] = FONT[idx + 3]
        buf[offset + 4] = FONT[idx + 4]
        offset += 6  # 5 pixels + 1 pixel gap

def clear_page(page):
    """Clear one page (8 pixel rows) -- much faster than fill(0)."""
    start = page * 128
    for i in range(128):
        buf[start + i] = 0

def clear_pages(start_page, end_page):
    """Clear a range of pages."""
    for p in range(start_page, end_page + 1):
        clear_page(p)

# -- Benchmark ---------------------------------------------------------

def benchmark(name, func, iterations=50):
    start = time.monotonic()
    for _ in range(iterations):
        func()
    elapsed = time.monotonic() - start
    fps = iterations / elapsed
    ms = (elapsed / iterations) * 1000
    print(name + ": " + str(round(fps, 1)) + " FPS (" + str(round(ms, 1)) + " ms/frame)")

print("=" * 40)
print("  Fast OLED Benchmark (1MHz I2C)")
print("=" * 40)

# Test 1: fast_text 1 line + show
print("\n[1] fast_text 1 line + show...")
def one_line():
    clear_page(0)
    fast_text("Hello World", 0, 0)
    oled.show()
benchmark("1 fast line", one_line)

# Test 2: fast_text 7 lines + show (same as slow benchmark)
print("\n[2] fast_text 7 lines + show...")
def seven_lines():
    clear_pages(0, 6)
    fast_text("DMX Controller", 0, 0)
    fast_text("----------------", 0, 1)
    fast_text("X: +50 Y: -30", 0, 2)
    fast_text("Z: CW  =====", 0, 3)
    fast_text("Dir: R U", 0, 4)
    fast_text("Btn:B1 #5", 0, 5)
    fast_text("FPS: 99.9", 0, 6)
    oled.show()
benchmark("7 fast lines", seven_lines)

# Test 3: comparison with oled.text()
print("\n[3] oled.text() 7 lines (for comparison)...")
def seven_slow():
    oled.fill(0)
    oled.text("DMX Controller", 0, 0, 1)
    oled.text("----------------", 0, 9, 1)
    oled.text("X: +50 Y: -30", 0, 18, 1)
    oled.text("Z: CW  =====", 0, 27, 1)
    oled.text("Dir: R U", 0, 36, 1)
    oled.text("Btn:B1 #5", 0, 45, 1)
    oled.text("FPS: 99.9", 0, 54, 1)
    oled.show()
benchmark("7 slow lines", seven_slow)

# Test 4: partial update -- only redraw 4 dynamic lines
print("\n[4] Partial update (4 dynamic lines only)...")
# Pre-render static header once
clear_pages(0, 7)
fast_text("DMX Controller", 0, 0)
fast_text("----------------", 0, 1)
oled.show()

def partial_update():
    clear_pages(2, 6)
    fast_text("X: +50 Y: -30", 0, 2)
    fast_text("Z: CW  =====", 0, 3)
    fast_text("Dir: R U", 0, 4)
    fast_text("Btn:B1 #5", 0, 5)
    oled.show()
benchmark("4 dynamic", partial_update)

print("\nDone!")

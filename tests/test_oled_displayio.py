# test_oled_displayio.py -- SSD1306 OLED test using displayio (native C driver)
# ============================================================================
# Uses displayio + terminalio instead of adafruit_framebuf.
# displayio is built into CircuitPython (no .mpy needed) and runs in C,
# so screen updates are MUCH faster than the framebuf Python implementation.
#
# Requires: adafruit_displayio_ssd1306.mpy in CIRCUITPY/lib/
#           (different from adafruit_ssd1306.mpy used in framebuf version)
# Does NOT need font5x8.bin -- terminalio has a built-in font.
#
# Wiring: SDA=D4, SCL=D5, VCC=3.3V, GND=GND
# I2C address: 0x3C (default for most SSD1306 128x64)

import board
import busio
import displayio
import terminalio
import time
from adafruit_display_text import label as text_label
import adafruit_displayio_ssd1306

# -- Release any previous display (needed if restarting without power cycle) --
displayio.release_displays()

# -- I2C + Display setup -----------------------------------------------
# 400kHz I2C for fast framebuffer transfer
i2c = busio.I2C(scl=board.D5, sda=board.D4, frequency=400000)
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)

# SSD1306 128x64 OLED
# auto_refresh=True means displayio handles screen updates automatically
# when the display group is modified -- no manual show() needed
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# -- Build the display layout -------------------------------------------
# displayio uses a tree of Groups and TileGrids.
# We create text labels and add them to a group.
# When we update label.text, displayio only redraws the changed parts.

root = displayio.Group()
display.root_group = root

# Static header
header = text_label.Label(
    terminalio.FONT,
    text="DMX Controller",
    color=0xFFFFFF,
    x=0, y=5
)
root.append(header)

separator = text_label.Label(
    terminalio.FONT,
    text="----------------",
    color=0xFFFFFF,
    x=0, y=15
)
root.append(separator)

# Dynamic labels -- we update .text on these each frame
xy_label = text_label.Label(
    terminalio.FONT,
    text="X:  +0 Y:  +0",
    color=0xFFFFFF,
    x=0, y=25
)
root.append(xy_label)

z_label = text_label.Label(
    terminalio.FONT,
    text="Z: ---",
    color=0xFFFFFF,
    x=0, y=35
)
root.append(z_label)

dir_label = text_label.Label(
    terminalio.FONT,
    text="Dir: - -",
    color=0xFFFFFF,
    x=0, y=45
)
root.append(dir_label)

info_label = text_label.Label(
    terminalio.FONT,
    text="displayio test",
    color=0xFFFFFF,
    x=0, y=55
)
root.append(info_label)

# -- Test: counter + FPS measurement ------------------------------------
print("displayio OLED test -- measuring FPS")
print("Ctrl+C to stop")

count = 0
fps_start = time.monotonic()
fps_frames = 0

try:
    while True:
        count += 1
        fps_frames += 1

        # Update dynamic labels (displayio handles dirty-region refresh)
        xy_label.text = "Count: " + str(count)

        # Cycle through some Z text to test update speed
        if count % 3 == 0:
            z_label.text = "Z: CW  ====="
        elif count % 3 == 1:
            z_label.text = "Z: CCW ====="
        else:
            z_label.text = "Z: ---"

        dir_label.text = "Frame: " + str(fps_frames)

        # Calculate and display FPS every second
        elapsed = time.monotonic() - fps_start
        if elapsed >= 1.0:
            fps = fps_frames / elapsed
            info_label.text = "FPS: {:.1f}".format(fps)
            print("FPS: {:.1f}".format(fps))
            fps_frames = 0
            fps_start = time.monotonic()

        # Small delay -- displayio auto-refreshes, but we need to
        # give it time to actually push the framebuffer
        time.sleep(0.01)

except KeyboardInterrupt:
    info_label.text = "Test done!"
    print("\nDone. Final count: " + str(count))

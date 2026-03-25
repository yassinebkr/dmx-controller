# test_oled_displayio.py -- SSD1306 OLED test using displayio (native C driver)
# ============================================================================
# CircuitPython 10.x uses built-in busdisplay + i2cdisplaybus.
# No external SSD1306 library needed -- just the init sequence bytes.
# Much faster than adafruit_framebuf (C vs Python rendering).
#
# Requires in CIRCUITPY/lib/:
#   - adafruit_display_text/ (folder)
#
# Wiring: SDA=D4, SCL=D5, VCC=3.3V, GND=GND
# I2C address: 0x3C

import board
import busio
import displayio
import terminalio
import time
from adafruit_display_text import label as text_label

# In CircuitPython 10.x, these replace the old displayio classes
try:
    import i2cdisplaybus
    import busdisplay
    NEW_API = True
except ImportError:
    # Fallback for CircuitPython 8.x/9.x
    NEW_API = False

# -- Release any previous display (needed after soft reboot) --------
displayio.release_displays()

# -- I2C + Display setup --------------------------------------------
i2c = busio.I2C(scl=board.D5, sda=board.D4, frequency=400000)

# SSD1306 128x64 init sequence (from datasheet)
# These bytes configure the display controller registers
INIT_SEQUENCE = (
    b"\xAE\x00"       # display off
    b"\xD5\x01\x80"   # set display clock div
    b"\xA8\x01\x3F"   # set multiplex (64-1)
    b"\xD3\x01\x00"   # set display offset = 0
    b"\x40\x00"        # set start line = 0
    b"\x8D\x01\x14"   # charge pump on
    b"\x20\x01\x00"   # memory mode = horizontal
    b"\xA1\x00"        # seg remap
    b"\xC8\x00"        # com scan dec
    b"\xDA\x01\x12"   # set com pins
    b"\x81\x01\xCF"   # set contrast
    b"\xD9\x01\xF1"   # set precharge
    b"\xDB\x01\x40"   # set vcomh deselect
    b"\xA4\x00"        # entire display ON (resume)
    b"\xA6\x00"        # normal display (not inverted)
    b"\xAF\x00"        # display on
)

if NEW_API:
    display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
    display = busdisplay.BusDisplay(
        display_bus,
        INIT_SEQUENCE,
        width=128,
        height=64,
        colstart=0,
        rowstart=0,
    )
else:
    display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
    display = displayio.Display(
        display_bus,
        INIT_SEQUENCE,
        width=128,
        height=64,
    )

# -- Build display layout --------------------------------------------
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

# Dynamic labels -- update .text each frame, displayio handles the rest
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

# -- FPS benchmark ---------------------------------------------------
print("displayio OLED test -- measuring FPS")
print("Ctrl+C to stop")

count = 0
fps_start = time.monotonic()
fps_frames = 0

try:
    while True:
        count += 1
        fps_frames += 1

        # Update dynamic labels
        xy_label.text = "Count: " + str(count)

        if count % 3 == 0:
            z_label.text = "Z: CW  ====="
        elif count % 3 == 1:
            z_label.text = "Z: CCW ====="
        else:
            z_label.text = "Z: ---"

        dir_label.text = "Frame: " + str(fps_frames)

        # FPS display every second
        elapsed = time.monotonic() - fps_start
        if elapsed >= 1.0:
            fps = fps_frames / elapsed
            info_label.text = "FPS: {:.1f}".format(fps)
            print("FPS: {:.1f}".format(fps))
            fps_frames = 0
            fps_start = time.monotonic()

        time.sleep(0.01)

except KeyboardInterrupt:
    info_label.text = "Test done!"
    print("\nDone. Final count: " + str(count))

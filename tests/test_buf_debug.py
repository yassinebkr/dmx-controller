# test_buf_debug.py -- Figure out actual buffer layout
# Traces oled.pixel() to see where bytes land in the buffer

import board, busio, adafruit_ssd1306

i2c = busio.I2C(scl=board.D5, sda=board.D4, frequency=400_000)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
buf = oled.buf

# Clear everything
oled.fill(0)

# Set ONE pixel at x=10, y=0
oled.pixel(10, 0, 1)

# Find which buffer byte changed
changed = []
for i in range(len(buf)):
    if buf[i] != 0:
        changed.append((i, buf[i]))

print("buf length:", len(buf))
print("pixel(10,0) changed:", changed)
print("Expected row-major: index=10, val=1")
print("Expected col-major: index=80, val=1")

# Clear and try another pixel
oled.fill(0)
oled.pixel(0, 8, 1)  # x=0, y=8 = page 1

changed2 = []
for i in range(len(buf)):
    if buf[i] != 0:
        changed2.append((i, buf[i]))

print("\npixel(0,8) changed:", changed2)
print("Expected row-major: index=128, val=1")
print("Expected col-major: index=1, val=1")

# One more: check stride
oled.fill(0)
oled.pixel(1, 8, 1)  # x=1, y=8

changed3 = []
for i in range(len(buf)):
    if buf[i] != 0:
        changed3.append((i, buf[i]))

print("\npixel(1,8) changed:", changed3)
print("Expected row-major: index=129, val=1")
print("Expected col-major: index=9, val=1")

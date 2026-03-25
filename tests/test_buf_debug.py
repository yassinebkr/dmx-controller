# test_buf_debug.py -- Compare oled.text() vs fast_text buffer output

import board, busio, adafruit_ssd1306

i2c = busio.I2C(scl=board.D5, sda=board.D4, frequency=400_000)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
buf = oled.buf

# Load font the same way as fast_text
with open("font5x8.bin", "rb") as f:
    raw = f.read()
if len(raw) == 1282:
    FONT = raw[2:]
else:
    FONT = raw

# Test 1: oled.text() writes 'A' at (0,0)
oled.fill(0)
oled.text("A", 0, 0, 1)
lib_bytes = [buf[i] for i in range(6)]
print("oled.text('A') -> buf[0:6]:", [hex(b) for b in lib_bytes])

# Test 2: what my FONT data says for 'A'
idx = ord('A') * 5
font_bytes = [FONT[idx + j] for j in range(5)]
print("FONT['A'] bytes:           ", [hex(b) for b in font_bytes])

# Test 3: same for 'D'
oled.fill(0)
oled.text("D", 0, 0, 1)
lib_bytes_d = [buf[i] for i in range(6)]
print("\noled.text('D') -> buf[0:6]:", [hex(b) for b in lib_bytes_d])

idx_d = ord('D') * 5
font_bytes_d = [FONT[idx_d + j] for j in range(5)]
print("FONT['D'] bytes:           ", [hex(b) for b in font_bytes_d])

# Test 4: check what library actually reads from font file
print("\nFont file size:", len(raw))
print("Header bytes:", [hex(b) for b in raw[:4]])
print("FONT size after strip:", len(FONT))

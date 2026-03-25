# Quick check: what is oled.buf?
import board, busio, adafruit_ssd1306
i2c = busio.I2C(scl=board.D5, sda=board.D4, frequency=400_000)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
print("buf length:", len(oled.buf))
print("buf[0]:", hex(oled.buf[0]))
print("buffer length:", len(oled.buffer))
print("buffer[0]:", hex(oled.buffer[0]))

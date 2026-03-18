# DMX Lyre Controller

Wireless DMX controller for a motorized lyre — school group project.

## Hardware

| Component | Role |
|-----------|------|
| Seeed XIAO RP2040 | Main controller (CircuitPython) |
| XBee S1 802.15.4 | Wireless radio (transparent UART) |
| SSD1306 128×64 OLED | Display (I2C) |
| 3-axis joystick | Pan/Tilt/Rotation control |
| 8 push buttons | DMX channel presets (resistor ladder on single ADC pin) |

## Pin Budget

| Pin | Function |
|-----|----------|
| A0 | Joystick X |
| A1 | Joystick Y |
| A2 | Joystick Z (rotation) |
| A3 | Button ladder (2kΩ pull-up) |
| D4 (SDA) | OLED data |
| D5 (SCL) | OLED clock |
| D6 (TX) | XBee DIN |
| D7 (RX) | XBee DOUT |

## Button Resistor Ladder

8 buttons on a single analog pin using individual resistors to GND with a 2kΩ pull-up to 3.3V.

| Button | Resistor | Voltage | ADC (16-bit) |
|--------|----------|---------|-------------|
| B1 | 0Ω | 0.000V | 0 |
| B2 | 220Ω | 0.327V | 6,494 |
| B3 | 560Ω | 0.722V | 14,338 |
| B4 | 1kΩ | 1.100V | 21,845 |
| B5 | 1.5kΩ | 1.414V | 28,086 |
| B6 | 2.7kΩ | 1.896V | 37,655 |
| B7 | 3.9kΩ | 2.183V | 43,351 |
| B8 | 6.8kΩ | 2.550V | 50,636 |

All E24 standard values. Minimum gap: 359 counts (22× noise margin).

## Project Structure

```
├── tests/           # Hardware test scripts
│   ├── test_oled.py
│   ├── test_buttons.py
│   └── test_combined.py
├── lib/             # CircuitPython libraries (not committed)
├── src/             # Main application code
├── docs/            # Wiring diagrams, datasheets
└── code.py          # Entry point (copy to CIRCUITPY)
```

## Setup

1. Install [CircuitPython](https://circuitpython.org/board/seeeduino_xiao_rp2040/) on the XIAO RP2040
2. Copy required libraries to `CIRCUITPY/lib/`:
   - `adafruit_ssd1306.mpy`
   - `adafruit_framebuf.mpy`
3. Copy a test script to `CIRCUITPY/code.py` to run it
4. Open serial console: `screen /dev/ttyACM0 115200`

## License

School project — private use.

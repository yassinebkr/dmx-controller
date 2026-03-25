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

## XBee Wireless Link

Point-to-point transparent UART between controller (XIAO) and receiver (PC).

| Setting | Controller (XIAO) | Receiver (PC USB-TTL) |
|---------|-------------------|----------------------|
| PAN ID | 1234 | 1234 |
| Channel | 12 | 12 |
| MY Address | 1 | 2 |
| Destination (DL) | 2 | 1 |
| Baud Rate | 9600 | 9600 |
| Mode | Transparent (AP=0) | Transparent (AP=0) |

- **Controller config:** run `config/xbee_setup.py` on the XIAO (once — saves to flash)
- **PC config:** use XCTU to set the matching values (see `config/XBEE_CONFIG.md`)
- **Firmware:** 8073 (XBee S1 802.15.4)

## Project Structure

```
├── config/          # Module configuration
│   ├── xbee_setup.py        # Run once to program controller XBee
│   └── XBEE_CONFIG.md       # Network settings for both modules
├── tests/           # Hardware test scripts
│   ├── test_oled.py
│   ├── test_buttons.py
│   ├── test_joystick.py
│   ├── test_combined.py
│   └── xbee_config_and_test.py
├── lib/             # CircuitPython libraries (not committed)
├── src/             # Main application code
├── docs/            # Datasheets, pinouts, project briefs
└── code.py          # Entry point (copy to CIRCUITPY)
```

## Setup

1. Install [CircuitPython](https://circuitpython.org/board/seeeduino_xiao_rp2040/) on the XIAO RP2040
2. Copy required libraries to `CIRCUITPY/lib/`:
   - `adafruit_ssd1306.mpy`
   - `adafruit_framebuf.mpy`
   - `font5x8.bin` (to CIRCUITPY root, not lib)
3. Configure XBee modules — see [XBee config](config/XBEE_CONFIG.md)
4. Copy a test script to `CIRCUITPY/code.py` to run it
5. Open serial console: `screen /dev/ttyACM0 115200`

## License

School project — private use.

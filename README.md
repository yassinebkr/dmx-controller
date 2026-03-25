# DMX Lyre Controller

Wireless DMX controller for a motorized lyre — school group project (BTS SN, Jules Ferry 2026).

## Hardware

| Component | Role |
|-----------|------|
| Seeed XIAO RP2040 | Main controller (CircuitPython) |
| XBee S1 802.15.4 | Wireless radio (transparent UART) |
| SSD1306 128×64 OLED | Display (I2C, 0x3C) |
| 3-axis joystick | Pan/Tilt/Rotation control (3 pots, no button) |
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

Currently wired: B1–B3. Remaining B4–B8 to be added.

## Joystick Calibration

| Axis | Min | Center | Max |
|------|-----|--------|-----|
| X | 489 | 31,979 | 63,522 |
| Y | 384 | 31,492 | 63,666 |
| Z | 438 | 3,490 | 36,000 |

Note: Z crosstalk on X/Y (~10-12 counts). CircuitPython ADC = 16-bit (0–65535).

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
dmx-controller/
├── config/                         # XBee module configuration
│   ├── XBEE_CONFIG.md              # Network settings reference (both modules)
│   ├── xbee_setup.py               # Full config script with verify (run once)
│   └── config_xbee.py              # Minimal config script
├── docs/                           # Datasheets & project briefs
│   ├── xbeemodule_ds.pdf           # XBee S1 datasheet
│   ├── rp2040_datasheet.pdf        # RP2040 datasheet
│   ├── xiaorp2040_pinout.jpg       # XIAO RP2040 pinout diagram
│   ├── XIAO-RP2040-pinout_sheet.xlsx
│   ├── ClubSpot 150 CT DMX charts.pdf
│   └── Fiche presentation projet E62 - *.pdf  # Project briefs
├── tests/                          # Hardware test scripts
│   ├── test_oled.py                # OLED display test
│   ├── test_buttons.py             # Button ladder ADC test
│   ├── test_joystick.py            # Joystick with auto-calibration
│   ├── test_combined.py            # All inputs + OLED display
│   ├── test_xbee.py                # XBee diagnostic (AT command check)
│   └── xbee_config_and_test.py     # XBee config + bidirectional comms test
├── src/                            # Main application (TODO)
├── lib/                            # CircuitPython libraries (not committed)
├── .gitignore
└── README.md
```

## Status

- [x] Joystick wiring + calibration (3-axis)
- [x] OLED SSD1306 I2C display
- [x] Button ladder (3/8 wired)
- [x] 5 test scripts (oled, buttons, joystick, combined, xbee)
- [x] XBee UART communication confirmed (firmware 8073)
- [x] XBee network configured (controller + PC receiver)
- [ ] Bidirectional XBee comms test
- [ ] Wire remaining 5 buttons (B4–B8)
- [ ] Main application (joystick + buttons → XBee → DMX)
- [ ] PCB layout (Proteus)

## Setup

1. Install [CircuitPython](https://circuitpython.org/board/seeeduino_xiao_rp2040/) on the XIAO RP2040
2. Copy required libraries to `CIRCUITPY/lib/`:
   - `adafruit_ssd1306.mpy`
   - `adafruit_framebuf.mpy`
3. Copy `font5x8.bin` to CIRCUITPY root (required for OLED text)
4. Configure XBee modules — see [XBee config](config/XBEE_CONFIG.md)
5. Copy a test script to `CIRCUITPY/code.py` to run it
6. Serial console: `screen /dev/ttyACM0 115200`

## License

School project — private use.

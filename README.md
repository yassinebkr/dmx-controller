# DMX Lyre Controller

Wireless DMX controller for a motorized lyre — school group project (BTS SN, Jules Ferry 2026).

## Hardware

| Component | Role |
|-----------|------|
| Seeed XIAO RP2040 | Main controller (CircuitPython) |
| XBee S1 802.15.4 | Wireless radio (transparent UART) |
| SSD1306 128×64 OLED | Display (I2C, 0x3C) |
| 3-axis joystick | Pan/Tilt/Rotation control (3 pots, spring-return) |
| 8 push buttons | DMX presets (resistor ladder on single ADC pin) |
| PEC12R-4115F-S0012 | Rotary encoder (A/B/pushbutton) |

## Architecture

Split PCB design:
- **Main PCB:** XIAO RP2040 + OLED + XBee + joystick connectors + power regulator
- **Daughterboard:** 8 buttons + resistor ladder + rotary encoder
- **Interconnect:** JST connectors + cables

## Pin Budget

| Pin | Function | Connector |
|-----|----------|-----------|
| A0/D0 | Joystick X | J2 |
| A1/D1 | Joystick Y | J3 |
| A2/D2 | Joystick Z (rotation) | J4 |
| A3/D3 | Button ladder (2.2kΩ pull-up) | J5 |
| D4 (SDA) | OLED data | J1 |
| D5 (SCL) | OLED clock | J1 |
| D6 (TX) | XBee DIN | — |
| D7 (RX) | XBee DOUT | — |
| D8 | Encoder B | J6 |
| D9 | Encoder A | J6 |
| D10 | Encoder pushbutton | J6 |

## Button Resistor Ladder

8 buttons on a single analog pin using individual resistors to GND with a **2.2kΩ pull-up** to 3.3V.

| Button | Resistor | Voltage | ADC (16-bit) | Threshold |
|--------|----------|---------|-------------|-----------|
| B1 | 0Ω | 0.000V | 0 | 0–2,978 |
| B2 | 220Ω | 0.300V | 5,957 | 2,979–9,626 |
| B3 | 560Ω | 0.670V | 13,296 | 9,627–16,887 |
| B4 | 1kΩ | 1.031V | 20,479 | 16,888–23,523 |
| B5 | 1.5kΩ | 1.338V | 26,568 | 23,524–31,339 |
| B6 | 2.7kΩ | 1.818V | 36,111 | 31,340–39,005 |
| B7 | 3.9kΩ | 2.110V | 41,899 | 39,006–45,707 |
| B8 | 6.8kΩ | 2.493V | 49,515 | 45,708–57,525 |
| Idle | 2.2kΩ (pull-up) | 3.300V | 65,535 | > 57,525 |

All E24 standard values. Minimum gap: 5,957 counts (B1→B2). With 16-bit ADC and 5-sample averaging, noise margin is excellent.

**Status:** Resistors soldered on daughterboard. Values confirmed working for B1–B3. B4–B8 need verification (thresholds updated in test scripts).

## Encoder

PEC12R-4115F-S0012 (HW-040) quadrature encoder with pushbutton.

| Pin | Function |
|-----|----------|
| A (ROT_A) | D9 |
| B (ROT_B) | D8 |
| Pushbutton (ROT_BTN) | D10 |
| Common | GND |

## Joystick Calibration

| Axis | Min | Center | Max |
|------|-----|--------|-----|
| X | 489 | 31,979 | 63,522 |
| Y | 384 | 31,492 | 63,666 |
| Z | 438 | 3,490 | 36,000 |

Note: Z crosstalk on X/Y (~10-12 counts). CircuitPython ADC = 16-bit (0–65535).

## XBee Wireless Link

Point-to-point transparent UART between controller (XIAO) and receiver (other student's board).

| Setting | Controller (XIAO) | Receiver |
|---------|-------------------|----------|
| PAN ID | 1234 | 1234 |
| Channel | 12 | 12 |
| MY Address | 1 | 2 |
| Destination (DL) | 2 | 1 |
| Baud Rate | 9600 | 9600 |
| Mode | Transparent (AP=0) | Transparent (AP=0) |

- **Controller config:** run `config/xbee_setup.py` on the XIAO (once — saves to flash)
- **Receiver config:** see `docs/PROTOCOL.md` for packet format
- **Firmware:** 8073 (XBee S1 802.15.4)

## Protocol

Wireless protocol specification: [`docs/PROTOCOL.md`](docs/PROTOCOL.md)

- **DMX Mode 2** — 8 channels (Pan, Tilt, Pan Fine, Tilt Fine, Speed, Color, Gobo, Shutter)
- **10-byte binary packet** — 8 DMX values + sequence + checksum
- **20Hz update rate** with delta filtering + 500ms heartbeat
- **Velocity mode** joystick (spring-return compatible)

## Project Structure

```
dmx-controller/
├── config/                         # XBee module configuration
│   ├── XBEE_CONFIG.md              # Network settings reference
│   └── xbee_setup.py               # Config script — run once, saves to flash
├── docs/                           # Datasheets, protocol, project briefs
│   ├── PROTOCOL.md                 # Wireless protocol specification (v1.0)
│   ├── xbeemodule_ds.pdf           # XBee S1 datasheet
│   ├── rp2040_datasheet.pdf        # RP2040 datasheet
│   ├── xiaorp2040_pinout.jpg       # XIAO RP2040 pinout
│   ├── ClubSpot 150 CT DMX charts.pdf
│   └── Fiche presentation projet E62 - *.pdf
├── tests/                          # Hardware test scripts
│   ├── test_oled.py                # OLED display test
│   ├── test_buttons.py             # Button ladder ADC test (8 buttons, 2.2k pull-up)
│   ├── test_joystick.py            # Joystick with auto-calibration
│   ├── test_combined.py            # All inputs + OLED display
│   ├── test_xbee.py                # XBee bidirectional comms test
│   ├── test_ec11.py                # Rotary encoder (quadrature + pushbutton)
│   ├── test_oled_fast.py           # Fast framebuffer benchmark
│   ├── test_oled_speed.py          # I2C bottleneck isolation
│   ├── test_oled_displayio.py      # displayio alternative test
│   └── test_buf_debug.py           # Font/buffer diagnostic
├── src/                            # Main application (TODO)
├── lib/                            # CircuitPython libraries (not committed)
├── .gitignore
└── README.md
```

## Status

- [x] Joystick wiring + calibration (3-axis, spring-return)
- [x] OLED SSD1306 I2C display
- [x] Button ladder (PCB received, resistors not soldered)
- [x] Encoder (PEC12R, PCB mounted)
- [x] Test scripts (oled, buttons, joystick, combined, xbee, fast, speed, displayio, buf, ec11)
- [x] XBee UART confirmed (firmware 8073)
- [x] XBee network configured (PAN 1234, MY=1/DL=2)
- [x] PCBs fabricated (CNC-milled, single-sided, through-hole)
- [x] Wireless protocol defined (Mode 2, 10-byte packet, 20Hz)
- [x] Resistors soldered on daughterboard (values: idle 2.2k, B1 0Ω, B2 220Ω, B3 560Ω, B4 1kΩ, B5 1.5kΩ, B6 2.7kΩ, B7 3.9kΩ, B8 6.8kΩ)
- [ ] Main application (src/main.py)
- [ ] Integration test with receiver board

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

# DMX Controller Protocol Specification

## Overview

Wireless DMX controller for ClubSpot 150 CT motorized lyre. Controller (XIAO RP2040 + XBee) sends commands to receiver board (other student) which translates to DMX512.

## DMX Mode

**Mode 2 — 8 channels** (selected for separate Gobo + Shutter control)

| DMX Ch | Function | Range | Control Type |
|--------|----------|-------|--------------|
| 1 | Pan | 0-255 | proportional |
| 2 | Tilt | 0-255 | proportional |
| 3 | Pan Fine | 0-255 | proportional |
| 4 | Tilt Fine | 0-255 | proportional |
| 5 | Speed | 0-255 | step/proportional |
| 6 | Color | 0-255 | proportional |
| 7 | Gobo | 0-255 | step/proportional |
| 8 | Shutter/Strobe/Reset | 0-255 | step/proportional |

## Wireless Packet Format

Fixed 10-byte binary packet over XBee transparent UART (9600 baud).

| Byte | Field | Range | Description |
|------|-------|-------|-------------|
| 0 | Pan coarse | 0-255 | 128 = center/stop |
| 1 | Tilt coarse | 0-255 | 128 = center/stop |
| 2 | Pan fine | 0-255 | 128 = center |
| 3 | Tilt fine | 0-255 | 128 = center |
| 4 | Speed | 0-255 | See speed table below |
| 5 | Color | 0-255 | See color table below |
| 6 | Gobo | 0-255 | See gobo table below |
| 7 | Shutter | 0-255 | See shutter table below |
| 8 | Sequence | 0-255 | Wraps around, detect packet drops |
| 9 | Checksum | 0-255 | XOR of bytes 0-8 |

### Checksum Calculation

```python
checksum = pan ^ tilt ^ pan_fine ^ tilt_fine ^ speed ^ color ^ gobo ^ shutter ^ sequence
```

### Transmission Rules

- **Active:** Send every 50ms (20Hz) when any value changed since last packet
- **Idle:** Skip packets if joystick centered AND no button/encoder activity
- **Heartbeat:** Send one packet every 500ms when idle (maintains link)
- **Receiver:** Validate checksum, check sequence number gap, output to DMX 1-8

## Control Mapping

### Joystick (Velocity Mode)

Spring-return joystick — center position = stop. Deflection controls speed, not absolute position.

| Axis | Function | Behavior |
|------|----------|----------|
| X | Pan | Left/right = pan direction + speed. Center = stop. |
| Y | Tilt | Up/down = tilt direction + speed. Center = stop. |
| Z (rotation) | Speed | CW = increase speed, CCW = decrease. Center = hold current. |

### Encoder (PEC12R-4115F-S0012)

| Action | Function |
|--------|----------|
| Rotate CW | Next color |
| Rotate CCW | Previous color |
| Push button | Cycle shutter: open → strobe → pulse+ → pulse- → random → closed → open |

### Buttons (Resistor Ladder)

| Button | Function | DMX Value |
|--------|----------|-----------|
| B1 | Color: White | 0 |
| B2 | Color: Red | 21 |
| B3 | Color: Blue | 85 |
| B4 | Color: Green | 74 |
| B5 | Gobo: Open | 0 |
| B6 | Gobo: Rotate | 228 |
| B7 | Shutter: Open | 64 |
| B8 | Shutter: Strobe | 96 |

## DMX Value Tables

### Speed (Channel 5)

| Value | Function |
|-------|----------|
| 0-7 | Max speed (tracking mode) |
| 8-249 | Vector speed (proportional, max→min) |
| 250-252 | Max speed tracking + blackout on color/gobo change |
| 253-255 | Max speed vector + blackout on movement/color/gobo change |

### Color (Channel 6)

| Value | Color |
|-------|-------|
| 0-7 | Open/white |
| 8-15 | Turquoise |
| 16-23 | Red |
| 24-31 | Cyan |
| 32-39 | Light green |
| 40-47 | Magenta |
| 48-55 | Light blue |
| 56-63 | Yellow |
| 64-71 | Green |
| 72-79 | Pink |
| 80-87 | Blue |
| 88-95 | Orange |
| 96-189 | Forward rainbow (fast→slow) |
| 190-193 | No rotation |
| 194-255 | Backward rainbow (slow→fast) |

### Gobo (Channel 7)

| Value | Function |
|-------|----------|
| 0-7 | Open position (hole) |
| 8-15 | Gobo 1 |
| 16-23 | Gobo 2 |
| 24-31 | Gobo 3 |
| 32-39 | Gobo 4 |
| 40-47 | Gobo 5 |
| 48-55 | Gobo 6 |
| 56-63 | Gobo 7 |
| 64-71 | Gobo 8 |
| 72-79 | Gobo 9 |
| 80-87 | Gobo 10 |
| 88-95 | Gobo 11 |
| 96-227 | Shaking gobos with variable speed |
| 228-255 | Gobo wheel rotation (slow→fast) |

### Shutter/Strobe/Reset (Channel 8)

| Value | Function |
|-------|----------|
| 0 | Shutter closed |
| 1-63 | Light intensity 0-100% (dimmer) |
| 64-95 | Shutter open |
| 96-127 | Strobe effect (slow→fast, max 8 flashes/s) |
| 128-139 | Reset |
| 140-159 | Shutter closed |
| 160-175 | Pulse effect (increasing speed) |
| 176-191 | Pulse effect (decreasing speed) |
| 192-223 | Random strobe (increasing speed) |
| 224-255 | Shutter open |

## Hardware

### Main PCB
- XIAO RP2040 (CircuitPython)
- SSD1306 128×64 OLED (I2C, 0x3C)
- XBee S1 802.15.4 (transparent UART, 9600 baud)
- AP2112K-3.3 LDO regulator
- JST connectors for all peripherals

### Daughterboard
- 8 push buttons with resistor ladder (single analog input)
- PEC12R-4115F-S0012 rotary encoder (A/B/pushbutton)
- 2kΩ pull-up resistor
- JST connector to mainboard

### Pin Mapping

| Pin | Function | Connector |
|-----|----------|-----------|
| A0/D0 | Joystick X | J2 |
| A1/D1 | Joystick Y | J3 |
| A2/D2 | Joystick Z | J4 |
| A3/D3 | Buttons (resistor ladder) | J5 |
| D4 | OLED SDA | J1 |
| D5 | OLED SCL | J1 |
| D6 | XBee TX (to XBee DIN) | U1 |
| D7 | XBee RX (from XBee DOUT) | U1 |
| D8 | Encoder B | J6 |
| D9 | Encoder A | J6 |
| D10 | Encoder pushbutton | J6 |

### XBee Network
- PAN ID: 1234
- Channel: 12
- Controller MY: 1, DL: 2
- Receiver MY: 2, DL: 1
- Baud: 9600, Transparent mode (AP=0)

## Receiver Implementation Notes

1. Parse 10-byte packets from UART
2. Validate checksum (XOR of bytes 0-8 == byte 9)
3. Check sequence number — if gap > 1, packet(s) were dropped
4. Map bytes 0-7 directly to DMX channels 1-8
5. Output DMX512 at 44Hz (standard) or 25Hz

## Version

Protocol v1.0 — 2026-05-26

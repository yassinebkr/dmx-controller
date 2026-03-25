# XBee S1 802.15.4 — Network Configuration

Two XBee modules in point-to-point transparent UART mode.

## Network Settings

| Parameter | Controller (XIAO) | Receiver (PC USB-TTL) |
|-----------|-------------------|----------------------|
| PAN ID (ID) | 1234 | 1234 |
| Channel (CH) | 12 (0x0C) | 12 (0x0C) |
| MY Address | 1 | 2 |
| DL (Destination) | 2 | 1 |
| DH | 0 | 0 |
| Baud Rate (BD) | 9600 | 9600 |
| API Mode (AP) | 0 (transparent) | 0 (transparent) |
| Firmware | 8073 | 8073 |

## How to Configure

### Controller (XIAO RP2040)

Copy `config/xbee_setup.py` to `CIRCUITPY/code.py` and run once.
The script enters AT command mode, writes all parameters, verifies them,
and saves to flash (ATWR). Settings persist across power cycles.

To change values, edit the variables at the top of `xbee_setup.py`:
```python
PAN_ID    = "1234"   # Network ID
CHANNEL   = "0C"     # Channel 12 (hex)
MY_ADDR   = "1"      # This module's address
DEST_ADDR = "2"      # Target module's address
BAUD      = "3"      # 9600 baud
```

### Receiver (PC)

Use **XCTU** software:
1. Connect the USB-TTL adapter with XBee
2. Add module (9600 baud, 8N1)
3. Set: ID=1234, CH=C, MY=2, DL=1, DH=0
4. Click **Write** to save to flash

## Testing

After configuring both modules:
1. Open XCTU Console on the PC module
2. Copy `tests/test_xbee.py` to `CIRCUITPY/code.py`
3. "Hello from XIAO #0" through #4 should appear in XCTU Console
4. Type in XCTU Console — text appears in XIAO serial output

## Notes

- **Transparent mode (AP=0):** data sent to UART goes straight out over the air. No framing needed.
- **Channel:** 12 decimal = 0x0C. Valid range: 11–26 (0x0B–0x1A).
- **PAN ID:** 1234. Valid range: 0–65535.
- **Settings persist** across power cycles after ATWR (write to flash).
- **Factory reset:** enter command mode (`+++`), send `ATRE\r`, then `ATWR\r`.
- **Max RF payload:** 100 bytes per packet. DMX lyre needs ~20 channels = 20 bytes — fits easily.

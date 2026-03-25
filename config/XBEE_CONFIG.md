# XBee S1 802.15.4 — Network Configuration

Two XBee S1 modules (firmware 8073) in point-to-point transparent UART mode.

## Network Settings

| Parameter | Controller (XIAO) | Receiver (PC USB-TTL) |
|-----------|-------------------|----------------------|
| PAN ID (ID) | 1234 | 1234 |
| Channel (CH) | 12 | 12 |
| MY Address | 1 | 2 |
| DL (Destination) | 2 | 1 |
| DH | 0 | 0 |
| Baud Rate | 9600 | 9600 |
| Mode (AP) | 0 (transparent) | 0 (transparent) |

## How to Configure

### Controller (XIAO RP2040)

1. Copy `config/xbee_setup.py` to `CIRCUITPY/code.py`
2. Run once — it programs the XBee and saves to flash
3. Replace `code.py` with your actual application after

To change values, edit the variables at the top of `xbee_setup.py`:
```python
PAN_ID    = "1234"   # Network ID — must match both modules
CHANNEL   = "0C"     # Channel 12 (hex) — must match both modules
MY_ADDR   = "1"      # This module's address (controller)
DEST_ADDR = "2"      # Target module's address (PC receiver)
BAUD      = "3"      # Baud rate index: 3 = 9600
```

### Receiver (PC via XCTU)

1. Connect the USB-TTL adapter with XBee module
2. Open XCTU, add module (9600 baud, 8N1)
3. Set: **ID=1234, CH=C, MY=2, DL=1, DH=0**
4. Click **Write** to save to flash

## Testing

After both modules are configured:
1. Open XCTU Console on the PC
2. Copy `tests/test_xbee.py` to `CIRCUITPY/code.py`
3. "Hello from XIAO #0" through #4 should appear in XCTU Console
4. Type in XCTU Console — text appears in XIAO serial output

## Reference

- **Transparent mode (AP=0):** UART data goes straight over the air — no framing needed
- **Channel range:** 11–26 (0x0B–0x1A)
- **PAN ID range:** 0–65535
- **Max RF payload:** 100 bytes/packet (DMX lyre needs ~20 bytes — fits easily)
- **Settings persist** across power cycles after ATWR
- **Factory reset:** command mode (`+++`) → `ATRE\r` → `ATWR\r`

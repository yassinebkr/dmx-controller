# XBee S1 802.15.4 — Network Configuration

Two XBee modules in point-to-point transparent UART mode.

## Network Settings

| Parameter | Controller (XIAO) | Receiver (PC USB-TTL) |
|-----------|-------------------|----------------------|
| PAN ID (ID) | 1234 | 1234 |
| Channel (CH) | 12 | 12 |
| MY Address | 1 | 2 |
| DL (Destination) | 2 | 1 |
| DH | 0 | 0 |
| Baud Rate (BD) | 9600 | 9600 |
| API Mode (AP) | 0 (transparent) | 0 (transparent) |

## How to Configure

### Controller (XIAO RP2040)
Copy `config/xbee_setup.py` to `CIRCUITPY/code.py` and run once.
The script programs the XBee via AT commands and saves to flash.

### Receiver (PC)
Use **XCTU** software:
1. Connect the USB-TTL adapter with XBee
2. Add module (9600 baud, 8N1)
3. Set: ID=1234, CH=C, MY=2, DL=1, DH=0
4. Click Write to save

## Verification

After configuring both modules:
1. Open XCTU Console on the PC module
2. Run `tests/xbee_config_and_test.py` on the XIAO
3. You should see "Hello from XIAO #0" through #4 in the XCTU Console
4. Type in XCTU Console — text should appear in the XIAO serial output

## Notes

- **Transparent mode (AP=0):** data sent to UART goes straight out over the air. No framing needed.
- **Channel:** 12 decimal = 0x0C. Valid range: 11–26 (0x0B–0x1A).
- **PAN ID:** 1234. Valid range: 0–65535.
- **Settings persist** across power cycles after ATWR (write to flash).
- To factory reset a module: enter command mode (`+++`), send `ATRE\r`, then `ATWR\r`.

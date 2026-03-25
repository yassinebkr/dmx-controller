"""
XBee S1 802.15.4 — Module Configuration Script
================================================
Run ONCE on the XIAO RP2040 to program the controller-side XBee.
After running, the settings are saved to flash (ATWR) and persist
across power cycles. No need to re-run unless you change the config.

Network config must match on both modules — see XBEE_CONFIG.md.
"""

import time
import board
import busio

# ── XBee Network Configuration ──────────────────────────────────
# Change these values to match your setup.
# The PC-side module must be configured with the MIRROR values
# (MY/DL swapped) — see XBEE_CONFIG.md for details.

PAN_ID   = "1234"   # Network ID — must match both modules
CHANNEL  = "0C"     # Channel 12 (hex) — must match both modules
MY_ADDR  = "1"      # This module's 16-bit address (controller = 1)
DEST_ADDR = "2"     # Destination address (PC receiver = 2)
BAUD     = "3"      # Baud rate index: 3 = 9600 (default)

# ── End Configuration ────────────────────────────────────────────

uart = busio.UART(board.D6, board.D7, baudrate=9600, timeout=2)


def send_at(cmd):
    """Send an AT command and print the response."""
    uart.write(bytes(cmd + "\r", "utf-8"))
    time.sleep(0.5)
    resp = uart.read(64)
    if resp:
        txt = resp.decode().strip()
        print(f"  {cmd:12s} -> {txt}")
    else:
        print(f"  {cmd:12s} -> No response!")
    return resp


def enter_command_mode():
    """Enter AT command mode (1s guard → +++ → 1s wait)."""
    print("Entering command mode...")
    time.sleep(1.1)
    uart.write(b"+++")
    time.sleep(1.5)
    resp = uart.read(64)
    if resp and b"OK" in resp:
        print("  OK — command mode active")
        return True
    print("  FAILED — no OK response")
    return False


print("=" * 40)
print("  XBee S1 Configuration Script")
print("=" * 40)

if enter_command_mode():
    print("\nWriting parameters...")
    send_at(f"ATID{PAN_ID}")     # PAN ID
    send_at(f"ATCH{CHANNEL}")    # Channel
    send_at(f"ATMY{MY_ADDR}")    # Source address
    send_at(f"ATDL{DEST_ADDR}")  # Destination address
    send_at("ATDH0")             # Destination high = 0 (16-bit mode)
    send_at(f"ATBD{BAUD}")       # Baud rate

    print("\nVerifying...")
    send_at("ATID")
    send_at("ATCH")
    send_at("ATMY")
    send_at("ATDL")
    send_at("ATDH")
    send_at("ATBD")

    print("\nSaving to flash...")
    send_at("ATWR")

    print("\nExiting command mode...")
    send_at("ATCN")

    print("\n✓ Configuration complete!")
    print("  This module is now the CONTROLLER (MY=1, DL=2)")
    print("  Restart with your main application.")
else:
    print("\nCould not enter command mode.")
    print("Check wiring: D6(TX) -> XBee DIN, D7(RX) <- XBee DOUT")

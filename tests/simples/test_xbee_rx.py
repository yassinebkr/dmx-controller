"""
XBee S1 — Simple RX Test (DMX Receiver)
=======================================
Listens for incoming data on the XBee and prints it.
Upload to the receiver's XIAO RP2040.

Wiring (CORRECT — use these pins!):
    D6 (TX) -> XBee DIN
    D7 (RX) <- XBee DOUT

WARNING:
    D0 and D2 are NOT hardware-UART pins on the XIAO RP2040.
    If you wired XBee to D0/D2, move the wires to D6/D7 or
    busio.UART will fail with "Invalid pins".

Prerequisites:
    - Transparent mode (AP=0), baudrate 9600
    - PAN ID = 1234, MY = 2, DL = 1
"""

import time
import board
import busio

# --- CORRECT pins for XIAO RP2040 (hardware UART) ---
uart = busio.UART(board.D6, board.D7, baudrate=9600, timeout=0.1)

# --- WRONG pins (only if you are NOT on XIAO RP2040) ---
# If your board truly uses D0/D2 and supports UART on them,
# uncomment the line below and comment out the one above.
# NOTE: on XIAO RP2040 these are A0/A2 and busio.UART will FAIL.
# uart = busio.UART(board.D2, board.D0, baudrate=9600, timeout=0.1)

print("=" * 40)
print("  XBee RX TEST (Receiver)")
print("=" * 40)
print("Waiting for packets...")
print("Press Ctrl+C to stop.\n")

while True:
    data = uart.read(64)
    if data:
        try:
            text = data.decode("utf-8").strip()
            print("  << RECEIVED : " + text)
        except Exception:
            print("  << RECEIVED (raw) : " + str(data))
    time.sleep(0.05)

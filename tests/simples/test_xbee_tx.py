"""
XBee S1 — Simple TX Test (DMX Controller)
=========================================
Sends a test packet every second over the XBee radio.
Upload to the XIAO RP2040 on the controller side.

Wiring:
    D6 (TX) -> XBee DIN
    D7 (RX) <- XBee DOUT

Prerequisites (already done via xbee_setup.py):
    - Transparent mode (AP=0), baudrate 9600
    - PAN ID = 1234, MY = 1, DL = 2
"""

import time
import board
import busio

# UART to the XBee module
uart = busio.UART(board.D6, board.D7, baudrate=9600, timeout=1)

print("=" * 40)
print("  XBee TX TEST (Controller)")
print("=" * 40)
print("Sending a packet every 1 second...")
print("Press Ctrl+C to stop.\n")

counter = 0

while True:
    msg = "DMX-TX: test packet #" + str(counter) + "\n"
    uart.write(bytes(msg, "utf-8"))
    print("  >> SENT : " + msg.strip())
    counter += 1
    time.sleep(1.0)

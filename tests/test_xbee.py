"""
XBee S1 — Communication Test
==============================
Tests bidirectional UART comms between the controller (XIAO)
and the PC receiver. Both modules must be configured first:
  - Controller: run config/xbee_setup.py once
  - PC: configure via XCTU (see config/XBEE_CONFIG.md)

Usage:
  1. Copy this file to CIRCUITPY/code.py
  2. Open XCTU Console on the PC (connected to receiver XBee)
  3. Watch serial output — sends 5 test messages to PC
  4. Type in XCTU Console — text appears in serial output
"""

import time
import board
import busio

uart = busio.UART(board.D6, board.D7, baudrate=9600, timeout=2)

print("=" * 40)
print("  XBee Communication Test")
print("=" * 40)

# Step 1: Quick AT check to confirm module is responding
print("\n[1] Checking XBee module...")
time.sleep(1.1)
uart.write(b"+++")
time.sleep(1.5)
resp = uart.read(64)

if not resp or b"OK" not in resp:
    print("  FAIL — no response from XBee")
    print("  Check wiring: D6(TX)->DIN, D7(RX)<-DOUT")
    raise SystemExit

# Read current config
uart.write(b"ATMY\r")
time.sleep(0.3)
my = uart.read(64)

uart.write(b"ATDL\r")
time.sleep(0.3)
dl = uart.read(64)

uart.write(b"ATID\r")
time.sleep(0.3)
pan = uart.read(64)

print(f"  MY={my.decode().strip() if my else '?'}, "
      f"DL={dl.decode().strip() if dl else '?'}, "
      f"ID={pan.decode().strip() if pan else '?'}")

# Exit command mode
uart.write(b"ATCN\r")
time.sleep(0.3)
uart.read(64)

# Step 2: Send test messages
print("\n[2] Sending 5 test messages to PC...")
time.sleep(0.5)

for i in range(5):
    msg = f"Hello from XIAO #{i}\n"
    uart.write(bytes(msg, "utf-8"))
    print(f"  TX: {msg.strip()}")
    time.sleep(0.5)

# Step 3: Listen for incoming data from PC
print("\n[3] Listening for data from PC (type in XCTU Console)...")
print("    Press Ctrl+C to stop.\n")

while True:
    data = uart.read(64)
    if data:
        try:
            text = data.decode("utf-8", errors="replace").strip()
            print(f"  RX: {text}")
        except Exception:
            print(f"  RX (raw): {data}")
    time.sleep(0.1)

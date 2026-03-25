"""
XBee S1 — Bidirectional Communication Test
============================================
Purpose:
    Tests wireless UART communication between the controller (XIAO)
    and the PC receiver (USB-TTL adapter). Sends test messages from
    XIAO to PC, then listens for data coming back from PC.

Prerequisites:
    Both XBee modules must be configured BEFORE running this test:
    - Controller (XIAO): run config/xbee_setup.py once
    - Receiver (PC): configure via XCTU (see config/XBEE_CONFIG.md)

Usage:
    1. Copy this file to CIRCUITPY/code.py
    2. Open XCTU Console on the PC (connected to receiver XBee)
    3. Watch serial output — sends 5 test messages to PC
    4. Type in XCTU Console — text should appear in serial output

Expected results:
    - XCTU Console shows: "Hello from XIAO #0" through #4
    - Typing in XCTU Console shows as "RX: <text>" in serial output
"""

import time
import board
import busio

# Initialize UART — same pins as main application
# D6 (TX) -> XBee DIN (data TO radio), D7 (RX) <- XBee DOUT (data FROM radio)
uart = busio.UART(board.D6, board.D7, baudrate=9600, timeout=2)

print("=" * 40)
print("  XBee Communication Test")
print("=" * 40)

# ── Step 1: Verify XBee module is responding ─────────────────────
# Enter command mode and read current config to confirm the module
# is alive and properly configured before attempting wireless comms.
print("\n[1] Checking XBee module...")

# Enter AT command mode: 1s silence -> +++ -> 1s silence
time.sleep(1.1)
uart.write(b"+++")
time.sleep(1.5)
resp = uart.read(64)

if not resp or b"OK" not in resp:
    print("  FAIL — no response from XBee")
    print("  Check wiring: D6(TX)->DIN, D7(RX)<-DOUT")
    # Stop execution — no point testing comms if module is not responding
    raise SystemExit

# Read current network settings for display
# Each AT command without a value parameter returns the current setting
uart.write(b"ATMY\r")   # Read MY (this module's 16-bit address)
time.sleep(0.3)
my = uart.read(64)

uart.write(b"ATDL\r")   # Read DL (destination address)
time.sleep(0.3)
dl = uart.read(64)

uart.write(b"ATID\r")   # Read ID (PAN network ID)
time.sleep(0.3)
pan = uart.read(64)

# Display current config (decode bytes to string, fallback to '?' if empty)
my_str = my.decode().strip() if my else "?"
dl_str = dl.decode().strip() if dl else "?"
pan_str = pan.decode().strip() if pan else "?"
print("  MY=" + my_str + ", DL=" + dl_str + ", ID=" + pan_str)

# Exit command mode — MUST do this before sending data!
# In command mode, UART data goes to the AT interpreter, not over the air
uart.write(b"ATCN\r")
time.sleep(0.3)
uart.read(64)  # Consume the 'OK' response

# ── Step 2: Send test messages to PC ─────────────────────────────
# In transparent mode (AP=0), anything written to UART after exiting
# command mode is transmitted wirelessly to the destination module (DL).
# The PC-side XBee receives it and outputs to its UART -> XCTU Console.
print("\n[2] Sending 5 test messages to PC...")
time.sleep(0.5)  # Brief pause after exiting command mode

for i in range(5):
    msg = "Hello from XIAO #" + str(i) + "\n"
    uart.write(bytes(msg, "utf-8"))
    print("  TX: Hello from XIAO #" + str(i))
    time.sleep(0.5)  # Space out messages to avoid buffer overflow

# ── Step 3: Listen for incoming data ─────────────────────────────
# Anything typed in XCTU Console on the PC is sent over the air by
# the PC's XBee (its DL points to our MY address) and arrives here
# as UART data.
print("\n[3] Listening for data from PC (type in XCTU Console)...")
print("    Press Ctrl+C to stop.\n")

while True:
    data = uart.read(64)  # Read up to 64 bytes, returns None on timeout
    if data:
        try:
            text = data.decode("utf-8").strip()
            print("  RX: " + text)
        except Exception:
            # If data is not valid UTF-8, show raw bytes for debugging
            print("  RX (raw): " + str(data))
    time.sleep(0.1)  # Small delay to prevent busy-loop on CPU

"""
XBee S1 802.15.4 — Module Configuration Script
================================================
Purpose:
    Programs the CONTROLLER-side XBee module with network settings.
    Run ONCE on the XIAO RP2040 — settings are saved to flash (ATWR)
    and persist across power cycles.

How it works:
    1. Enters AT command mode (1s silence -> +++ -> 1s silence)
    2. Writes PAN ID, channel, addresses, baud rate
    3. Reads back each setting to verify
    4. Saves to flash with ATWR
    5. Exits command mode — module returns to transparent UART

Usage:
    Copy this file to CIRCUITPY/code.py and let it run once.
    After success, replace code.py with your main application.

Network config must match on both modules — see XBEE_CONFIG.md.
"""

import time
import board
import busio

# ── XBee Network Configuration ──────────────────────────────────
# These values define the wireless link between controller and receiver.
# The PC-side module must have MIRRORED MY/DL values.
# Example: controller MY=1,DL=2 <-> receiver MY=2,DL=1
#
# PAN_ID and CHANNEL must be identical on both modules.
# BAUD index: 0=1200, 1=2400, 2=4800, 3=9600, 4=19200, 5=38400, 6=57600, 7=115200

PAN_ID    = "1234"   # Network ID (0-65535) — must match both modules
CHANNEL   = "0C"     # Channel 12 in hex (valid: 0B-1A = 11-26) — must match both
MY_ADDR   = "1"   # This module's 16-bit address in hex (controller = 1)
DEST_ADDR = "2"   # Destination address in hex (PC receiver = 2)
BAUD      = "3"      # Baud rate index: 3 = 9600

# ── End Configuration ────────────────────────────────────────────

# Initialize UART on XIAO RP2040 pins:
#   D6 (TX) -> XBee DIN (pin 3)  — data TO the XBee
#   D7 (RX) <- XBee DOUT (pin 2) — data FROM the XBee
uart = busio.UART(board.D6, board.D7, baudrate=9600, timeout=2)


def send_at(cmd):
    """
    Send an AT command to the XBee and print the response.

    AT commands are sent as ASCII text followed by carriage return.
    The module responds with the value (for reads) or 'OK' (for writes).
    Returns the raw response bytes, or None if no response.
    """
    uart.write(bytes(cmd + "\r", "utf-8"))
    time.sleep(0.5)  # Wait for module to process and respond
    resp = uart.read(64)
    if resp:
        txt = resp.decode().strip()
        print("  " + cmd + " -> " + txt)
    else:
        print("  " + cmd + " -> No response!")
    return resp


def enter_command_mode():
    """
    Enter AT command mode.

    The XBee requires a specific sequence:
    1. At least 1 second of silence (guard time, GT=0x3E8 = 1000ms)
    2. Send '+++' (no carriage return!)
    3. At least 1 second of silence
    4. Module responds with 'OK'

    After entering command mode, you have 10 seconds between commands
    before the module auto-exits (configurable with CT command).
    """
    print("Entering command mode...")
    time.sleep(1.1)    # Guard time before +++
    uart.write(b"+++") # No \\r — this is NOT an AT command
    time.sleep(1.5)    # Guard time after +++
    resp = uart.read(64)
    if resp and b"OK" in resp:
        print("  OK — command mode active")
        return True
    print("  FAILED — no OK response")
    return False


# ── Main Script ──────────────────────────────────────────────────
# Wait 2 seconds on startup to guarantee guard time silence.
# Without this, a board restart can send serial output (boot messages)
# that breaks the 1-second silence required before +++.
print("=" * 40)
print("  XBee S1 Configuration Script")
print("=" * 40)
print("Waiting 2s for clean guard time...")
time.sleep(2)

if enter_command_mode():
    # Write all network parameters
    print("\nWriting parameters...")
    send_at("ATID" + PAN_ID)      # PAN ID — network identifier
    send_at("ATCH" + CHANNEL)     # Channel — radio frequency slot
    send_at("ATMY" + MY_ADDR)     # MY — this module's 16-bit address
    send_at("ATDL" + DEST_ADDR)   # DL — destination address low word
    send_at("ATDH0")              # DH — destination address high (0 = 16-bit mode)
    send_at("ATBD" + BAUD)        # BD — UART baud rate

    # Read back each setting to confirm they were written correctly
    print("\nVerifying...")
    send_at("ATID")   # Should return: 1234
    send_at("ATCH")   # Should return: C
    send_at("ATMY")   # Should return: 1
    send_at("ATDL")   # Should return: 2
    send_at("ATDH")   # Should return: 0
    send_at("ATBD")   # Should return: 3

    # Save all parameters to non-volatile flash memory
    # Without ATWR, settings are lost on power cycle
    print("\nSaving to flash...")
    send_at("ATWR")

    # Exit command mode — module returns to transparent UART operation
    # (data written to UART is now transmitted over the air)
    print("\nExiting command mode...")
    send_at("ATCN")

    print("\nConfiguration complete!")
    print("  Controller: MY=1, DL=2, PAN=1234, CH=12")
    print("  Replace code.py with your main application.")
else:
    print("\nCould not enter command mode.")
    print("Check wiring: D6(TX) -> XBee DIN, D7(RX) <- XBee DOUT")
    print("Make sure no data was sent in the last 1 second before running.")

import board
import busio
import time

uart = busio.UART(board.D6, board.D7, baudrate=9600, timeout=1)

def xbee_cmd(cmd):
    """Send AT command, return response"""
    uart.write(f"{cmd}\r".encode())
    time.sleep(0.1)
    resp = uart.read(64)
    return resp.decode().strip() if resp else None

# Enter command mode
time.sleep(1.1)          # Guard time (1s silence before +++)
uart.write(b"+++")       # Don't add \r here!
time.sleep(1.1)          # Guard time (1s silence after +++)
resp = uart.read(64)
print(f"CMD mode: {resp}")  # Should print b'OK'

# Configure Module B (controller)
print("ID:", xbee_cmd("ATID1234"))   # PAN ID — must match both modules
print("CH:", xbee_cmd("ATCH0C"))     # Channel 12 — must match both modules
print("MY:", xbee_cmd("ATMY1"))      # My address = 1 (controller)
print("DL:", xbee_cmd("ATDL2"))      # Send to address 2 (PC receiver)
print("DH:", xbee_cmd("ATDH0"))      # 16-bit addressing
print("BD:", xbee_cmd("ATBD3"))      # 9600 baud

# Save to flash (survives power cycle)
print("WR:", xbee_cmd("ATWR"))       # Write to flash

# Exit command mode
print("CN:", xbee_cmd("ATCN"))       # Back to transparent mode

print("Done! Controller XBee configured (MY=1, DL=2).")
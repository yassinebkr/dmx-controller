import time
import board
import busio

uart = busio.UART(board.D6, board.D7, baudrate=9600, timeout=2)

def send_at(cmd):
    uart.write(bytes(cmd + "\r", "utf-8"))
    time.sleep(0.5)
    resp = uart.read(64)
    if resp:
        print(f"  {cmd} -> {resp}")
    else:
        print(f"  {cmd} -> No response")
    return resp

print("=== XBee Config ===")
print("Entering command mode...")
time.sleep(1.1)
uart.write(b"+++")
time.sleep(1.5)
resp = uart.read(64)
print(f"  +++ -> {resp}")

if resp and b"OK" in resp:
    print("\nSetting parameters...")
    send_at("ATID1234")   # PAN ID
    send_at("ATCH0C")     # Channel 12
    send_at("ATMY1")      # My address = 1
    send_at("ATDL2")      # Destination = 2 (PC)
    send_at("ATDH0")      # DH = 0
    send_at("ATWR")       # Write to flash
    send_at("ATCN")       # Exit command mode

    print("\n=== Config saved! Sending test... ===")
    time.sleep(1)

    for i in range(5):
        msg = f"Hello from XIAO #{i}\n"
        uart.write(bytes(msg, "utf-8"))
        print(f"Sent: {msg.strip()}")
        time.sleep(1)
        rx = uart.read(64)
        if rx:
            print(f"Received: {rx}")
else:
    print("Failed to enter command mode!")

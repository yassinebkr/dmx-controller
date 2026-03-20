import board
import busio
import time
import analogio

# === Step 1: Check XBee power ===
# If you have XBee VCC routed through a readable pin, check it
# Otherwise just visually confirm: is the XBee power LED on?
print("=== XBee Diagnostic ===")
print("Check: Is the XBee power LED on? (small red LED on module)")
print()

# === Step 2: Try both TX/RX orientations ===
for label, tx_pin, rx_pin in [
    ("Normal (D6=TX, D7=RX)", board.D6, board.D7),
    ("Swapped (D7=TX, D6=RX)", board.D7, board.D6),
]:
    print(f"--- Trying {label} ---")
    uart = busio.UART(tx_pin, rx_pin, baudrate=9600, timeout=1.5)
    
    # Flush any garbage
    uart.read(128)
    time.sleep(0.5)
    
    # Enter command mode
    time.sleep(1.2)
    uart.write(b"+++")
    time.sleep(1.5)
    resp = uart.read(64)
    
    if resp:
        print(f"  GOT RESPONSE: {resp}")
        # Try reading firmware version
        uart.write(b"ATVR\r")
        time.sleep(0.3)
        vr = uart.read(64)
        print(f"  Firmware: {vr}")
        uart.write(b"ATCN\r")
        uart.read(64)
        uart.deinit()
        print("  >>> THIS orientation works! <<<")
        break
    else:
        print("  No response")
        uart.deinit()
    
    time.sleep(0.5)

else:
    # Neither orientation worked — try other baud rates
    print()
    print("--- Trying different baud rates (D6=TX, D7=RX) ---")
    for baud in [9600, 19200, 38400, 57600, 115200, 4800, 2400, 1200]:
        uart = busio.UART(board.D6, board.D7, baudrate=baud, timeout=1.5)
        uart.read(128)
        time.sleep(1.2)
        uart.write(b"+++")
        time.sleep(1.5)
        resp = uart.read(64)
        if resp:
            print(f"  Baud {baud}: GOT {resp}")
            uart.write(b"ATCN\r")
            uart.read(64)
            uart.deinit()
            print(f"  >>> XBee is at {baud} baud! <<<")
            break
        else:
            print(f"  Baud {baud}: nothing")
            uart.deinit()
        time.sleep(0.3)
    else:
        print()
        print("No response at any baud or orientation.")
        print("Check:")
        print("  1. XBee power LED is ON")
        print("  2. Wires are solid (not loose jumpers)")
        print("  3. XBee is seated fully in the breakout/socket")
        print("  4. VCC=3.3V and GND connected")
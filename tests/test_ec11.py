# test_ec11.py -- Rotary encoder (EC11 / PEC12R) test for XIAO RP2040
# ===================================================================
# Tests the quadrature encoder with pushbutton on pins D8/D9/D10.
#
# Wiring:
#   D8 (GPIO 8)  → Encoder B (ROT_B)
#   D9 (GPIO 9)  → Encoder A (ROT_A)
#   D10 (GPIO 10)→ Encoder pushbutton (ROT_BTN)
#   GND          → Encoder common
#
# PEC12R-4115F-S0012 (HW-040 compatible):
#   - 12 pulses per revolution (24 detents)
#   - Pushbutton on shaft
#   - No pull-ups needed (internal on XIAO, or use external)

import board
import digitalio
import time

# --- Pin setup --------------------------------------------------------
# Encoder A and B with internal pull-ups
rot_a = digitalio.DigitalInOut(board.D9)
rot_a.direction = digitalio.Direction.INPUT
rot_a.pull = digitalio.Pull.UP

rot_b = digitalio.DigitalInOut(board.D8)
rot_b.direction = digitalio.Direction.INPUT
rot_b.pull = digitalio.Pull.UP

# Pushbutton with internal pull-up
rot_btn = digitalio.DigitalInOut(board.D10)
rot_btn.direction = digitalio.Direction.INPUT
rot_btn.pull = digitalio.Pull.UP

# --- State ------------------------------------------------------------
position = 0
last_a = rot_a.value
btn_pressed = False

print("=" * 40)
print("EC11 ENCODER TEST")
print("=" * 40)
print("Rotate encoder: CW/CCW position")
print("Press button: button state")
print("Ctrl+C to stop")
print()

# --- Main loop --------------------------------------------------------
try:
    while True:
        a = rot_a.value
        b = rot_b.value
        btn = not rot_btn.value  # Active low (pulled up, pressed = GND)

        # Quadrature decoding: detect edge on A, check B for direction
        if a != last_a and not a:  # Falling edge on A
            if b:
                position += 1
                print(f"  CW  → pos: {position}")
            else:
                position -= 1
                print(f"  CCW → pos: {position}")
        last_a = a

        # Button press detection (with simple debounce)
        if btn and not btn_pressed:
            print(f"  ▶ BUTTON PRESSED (pos: {position})")
            btn_pressed = True
        elif not btn and btn_pressed:
            print(f"  ▶ BUTTON RELEASED (pos: {position})")
            btn_pressed = False

        time.sleep(0.001)  # 1ms poll — encoder mechanical max ~2kHz

except KeyboardInterrupt:
    print(f"\nDone. Final position: {position}")

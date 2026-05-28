# test_ec11_v2.py -- Rotary encoder (EC11 / PEC12R) test for XIAO RP2040
# ===================================================================
# Tests the quadrature encoder with pushbutton on pins D8/D9/D10.
# This version adds raw pin state debugging to diagnose wiring issues.
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
#   - Internal pull-ups enabled (XIAO RP2040)

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
last_b = rot_b.value
btn_pressed = False

print("=" * 50)
print("EC11 ENCODER TEST v2 — with raw pin debug")
print("=" * 50)
print("Wiring check: all pins should read HIGH (1) when idle")
print("If any reads LOW (0) without interaction, check wiring")
print()

# --- Wiring check -----------------------------------------------------
print(f"Idle state: A={rot_a.value} B={rot_b.value} BTN={rot_btn.value}")
print("(Expected: A=1 B=1 BTN=1)")
print()

# --- Main loop --------------------------------------------------------
try:
    while True:
        a = rot_a.value
        b = rot_b.value
        btn_raw = rot_btn.value
        btn = not btn_raw  # Active low (pulled up, pressed = GND)

        # Quadrature decoding: 2x (both edges on A)
        if a != last_a:
            if a == b:
                position += 1
                print(f"  CW  → pos: {position}  (A={a} B={b})")
            else:
                position -= 1
                print(f"  CCW → pos: {position}  (A={a} B={b})")
        last_a = a

        # Also check B edge for missed transitions
        if b != last_b:
            # B changed without A change — possible missed A transition
            pass  # Already handled via A edge + state comparison
        last_b = b

        # Button press detection with debounce
        if btn and not btn_pressed:
            print(f"  ▶ BUTTON PRESSED (raw={btn_raw}, pos={position})")
            btn_pressed = True
        elif not btn and btn_pressed:
            print(f"  ▶ BUTTON RELEASED (raw={btn_raw}, pos={position})")
            btn_pressed = False

        time.sleep(0.001)  # 1ms poll

except KeyboardInterrupt:
    print(f"\nDone. Final position: {position}")

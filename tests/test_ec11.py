# test_ec11.py -- Rotary encoder (EC11 / PEC12R) test for XIAO RP2040
# ===================================================================
# Tests the quadrature encoder with pushbutton on pins D8/D9/D10.
# This version adds a raw value monitor to diagnose button issues.
#
# Wiring:
#   D8 (GPIO 2)  → Encoder B (ROT_B)
#   D9 (GPIO 4)  → Encoder A (ROT_A)
#   D10 (GPIO 3)→ Encoder pushbutton (ROT_BTN)
#   GND          → Encoder common
#
# PEC12R-4115F-S0012 (HW-040 compatible):
#   - 12 pulses per revolution (24 detents)
#   - Pushbutton on shaft (active LOW — connects to GND when pressed)
#   - Internal pull-ups enabled (XIAO RP2040)

import board
import digitalio
import time

# --- Pin setup --------------------------------------------------------
rot_a = digitalio.DigitalInOut(board.D9)
rot_a.direction = digitalio.Direction.INPUT
rot_a.pull = digitalio.Pull.UP

rot_b = digitalio.DigitalInOut(board.D8)
rot_b.direction = digitalio.Direction.INPUT
rot_b.pull = digitalio.Pull.UP

rot_btn = digitalio.DigitalInOut(board.D10)
rot_btn.direction = digitalio.Direction.INPUT
rot_btn.pull = digitalio.Pull.UP

# --- State ------------------------------------------------------------
position = 0
last_a = rot_a.value
last_b = rot_b.value
btn_pressed = False

print("=" * 50)
print("EC11 ENCODER TEST — Diagnostic")
print("=" * 50)
print()

# --- Wiring check -----------------------------------------------------
print("WIRING CHECK (idle state, no touching):")
print(f"  A (D9)  = {rot_a.value}  (should be 1 / HIGH)")
print(f"  B (D8)  = {rot_b.value}  (should be 1 / HIGH)")
print(f"  BTN(D10)= {rot_btn.value}  (should be 1 / HIGH — not pressed)")
print()

if rot_a.value == 0:
    print("  ⚠ A is LOW — check if D9 is shorted to GND")
if rot_b.value == 0:
    print("  ⚠ B is LOW — check if D8 is shorted to GND")
if rot_btn.value == 0:
    print("  ⚠ BTN is LOW — button may be stuck pressed or D10 shorted to GND")

print()
print("PHASE 1: Raw button monitor (press and hold the button)")
print("Press Ctrl+C to move to Phase 2")
print()

# Phase 1: Raw button value monitor
try:
    while True:
        btn_raw = rot_btn.value
        if btn_raw == 0:
            print(f"  BUTTON RAW = {btn_raw} (LOW — pressed detected!)")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n--- Moving to Phase 2 ---\n")

# --- Main loop --------------------------------------------------------
print("PHASE 2: Full encoder + button test")
print("Rotate encoder and press button. Ctrl+C to stop")
print()

try:
    while True:
        a = rot_a.value
        b = rot_b.value
        btn_raw = rot_btn.value
        btn = not btn_raw  # Active low

        # Detect ANY change
        changed = (a != last_a) or (b != last_b) or (btn != btn_pressed)

        if changed:
            # Show raw pin states
            states = f"A={a} B={b} BTN={btn_raw}({'PRESSED' if btn else 'released'})"

            # Encoder logic
            if a != last_a:
                if a == b:
                    position += 1
                    print(f"  CW  pos={position:3d}  |  {states}")
                else:
                    position -= 1
                    print(f"  CCW pos={position:3d}  |  {states}")
            elif b != last_b:
                # B changed without A — show it for debugging
                print(f"  B-only change  |  {states}")
            elif btn != btn_pressed:
                if btn:
                    print(f"  ▶ BUTTON PRESSED   |  {states}")
                else:
                    print(f"  ▶ BUTTON RELEASED  |  {states}")

            last_a = a
            last_b = b
            btn_pressed = btn

        time.sleep(0.001)

except KeyboardInterrupt:
    print(f"\nDone. Final position: {position}")

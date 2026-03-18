# test_joystick.py — 3-axis joystick test for XIAO RP2040
# Wiring: A0=X axis, A1=Y axis, A2=Z axis (rotation/pot)
#
# Most joystick modules output ~half VCC at rest (center position)
# CircuitPython ADC: 16-bit (0–65535)
# Center ≈ 32768, full left/down ≈ 0, full right/up ≈ 65535
#
# If your joystick has a push button (SW pin), wire it to a digital
# pin or include it in the button ladder on A3.

import board
import analogio
import time

joy_x = analogio.AnalogIn(board.A0)
joy_y = analogio.AnalogIn(board.A1)
joy_z = analogio.AnalogIn(board.A2)

# --- Phase 1: Raw values ---
# Move the joystick around and note the ranges
# This helps you calibrate deadzone and direction

print("=" * 50)
print("JOYSTICK RAW MONITOR")
print("=" * 50)
print("Move the joystick — note center, min, max values")
print("Ctrl+C to move to Phase 2")
print()

try:
    while True:
        x = joy_x.value
        y = joy_y.value
        z = joy_z.value
        print(f"X: {x:5d}  Y: {y:5d}  Z: {z:5d}")
        time.sleep(0.2)
except KeyboardInterrupt:
    print("\n--- Moving to Phase 2 ---\n")

# --- Phase 2: Mapped values with deadzone ---
# Adjust these after seeing Phase 1 readings

# Calibration: set these to your joystick's actual center readings
CENTER_X = 32768
CENTER_Y = 32768
CENTER_Z = 32768

# Deadzone: ignore small movements around center (noise/drift)
# ~5% of full range = 3277
DEADZONE = 3000

def map_axis(raw, center=32768, deadzone=DEADZONE):
    """Map raw 16-bit ADC to -100..+100 with deadzone.
    Returns 0 when in deadzone, negative for left/down, positive for right/up.
    """
    diff = raw - center
    if abs(diff) < deadzone:
        return 0
    # Map remaining range to -100..+100
    if diff > 0:
        return int((diff - deadzone) / (65535 - center - deadzone) * 100)
    else:
        return int((diff + deadzone) / (center - deadzone) * 100)

def direction_label(x, y):
    """Convert X/Y to a compass direction."""
    if x == 0 and y == 0:
        return "CENTER"
    parts = []
    if y > 20:
        parts.append("UP")
    elif y < -20:
        parts.append("DOWN")
    if x > 20:
        parts.append("RIGHT")
    elif x < -20:
        parts.append("LEFT")
    return "-".join(parts) if parts else "CENTER"

print("MAPPED JOYSTICK (deadzone={})".format(DEADZONE))
print("=" * 50)
print("Values: -100 to +100 (0 = center/deadzone)")
print("Ctrl+C to stop")
print()

try:
    while True:
        mx = map_axis(joy_x.value, CENTER_X)
        my = map_axis(joy_y.value, CENTER_Y)
        mz = map_axis(joy_z.value, CENTER_Z)
        direction = direction_label(mx, my)

        print(f"X:{mx:+4d}  Y:{my:+4d}  Z:{mz:+4d}  [{direction:>10s}]")
        time.sleep(0.15)
except KeyboardInterrupt:
    print("\nDone.")

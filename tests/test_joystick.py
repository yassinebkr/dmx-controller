# test_joystick.py — 3-axis joystick test for XIAO RP2040
# Wiring: A0=X axis, A1=Y axis, A2=Z axis (rotation)
# CircuitPython ADC: 16-bit (0–65535)
#
# This script has 3 phases:
#   Phase 1: Raw monitor (see what your joystick actually outputs)
#   Phase 2: Calibration (capture center + min/max per axis)
#   Phase 3: Mapped output using calibrated values

import board
import analogio
import time

joy_x = analogio.AnalogIn(board.A0)
joy_y = analogio.AnalogIn(board.A1)
joy_z = analogio.AnalogIn(board.A2)

def read_avg(pin, n=10):
    """Read ADC with averaging for stable values."""
    total = 0
    for _ in range(n):
        total += pin.value
        time.sleep(0.003)
    return total // n

# --- Phase 1: Raw values (10 seconds) ---
print("=" * 50)
print("PHASE 1: RAW MONITOR (10 seconds)")
print("=" * 50)
print("Move joystick around — watch the ranges")
print()

for i in range(50):
    x = read_avg(joy_x)
    y = read_avg(joy_y)
    z = read_avg(joy_z)
    print(f"X: {x:5d}  Y: {y:5d}  Z: {z:5d}")
    time.sleep(0.2)

# --- Phase 2: Calibration ---
print()
print("=" * 50)
print("PHASE 2: CALIBRATION")
print("=" * 50)

# Step 1: Read center (rest position)
print(">> Leave joystick at REST for 3 seconds...")
time.sleep(1)
samples_x = []
samples_y = []
samples_z = []
for _ in range(20):
    samples_x.append(read_avg(joy_x))
    samples_y.append(read_avg(joy_y))
    samples_z.append(read_avg(joy_z))
    time.sleep(0.1)

cx = sum(samples_x) // len(samples_x)
cy = sum(samples_y) // len(samples_y)
cz = sum(samples_z) // len(samples_z)
print(f"   Center: X={cx}  Y={cy}  Z={cz}")

# Step 2: Track min/max over 8 seconds of movement
print()
print(">> Move ALL axes to EXTREMES for 8 seconds!")
print("   (push X/Y to all corners, rotate Z fully both ways)")
time.sleep(0.5)

min_x, max_x = cx, cx
min_y, max_y = cy, cy
min_z, max_z = cz, cz

for i in range(80):
    x = read_avg(joy_x, 5)
    y = read_avg(joy_y, 5)
    z = read_avg(joy_z, 5)
    min_x = min(min_x, x)
    max_x = max(max_x, x)
    min_y = min(min_y, y)
    max_y = max(max_y, y)
    min_z = min(min_z, z)
    max_z = max(max_z, z)
    remaining = 8 - (i * 0.1)
    if i % 10 == 0:
        print(f"   {remaining:.0f}s remaining... X:[{min_x}-{max_x}] Y:[{min_y}-{max_y}] Z:[{min_z}-{max_z}]")
    time.sleep(0.1)

print()
print("CALIBRATION RESULTS:")
print(f"  X: min={min_x:5d}  center={cx:5d}  max={max_x:5d}")
print(f"  Y: min={min_y:5d}  center={cy:5d}  max={max_y:5d}")
print(f"  Z: min={min_z:5d}  center={cz:5d}  max={max_z:5d}")
print()
print("Copy these into your code:")
print(f"  CAL_X = ({min_x}, {cx}, {max_x})")
print(f"  CAL_Y = ({min_y}, {cy}, {max_y})")
print(f"  CAL_Z = ({min_z}, {cz}, {max_z})")
print()

# --- Phase 3: Mapped output using calibration ---

def map_calibrated(raw, cal_min, cal_center, cal_max, deadzone_pct=8):
    """Map raw ADC to -100..+100 using actual calibration values.
    deadzone_pct: percentage of range around center to treat as 0.
    """
    # Deadzone around center
    range_low = cal_center - cal_min
    range_high = cal_max - cal_center
    dz_low = int(range_low * deadzone_pct / 100)
    dz_high = int(range_high * deadzone_pct / 100)

    if cal_center - dz_low <= raw <= cal_center + dz_high:
        return 0

    if raw < cal_center - dz_low:
        # Negative side
        effective = cal_center - dz_low - raw
        full_range = range_low - dz_low
        if full_range <= 0:
            return 0
        return max(-100, -int(effective * 100 / full_range))
    else:
        # Positive side
        effective = raw - (cal_center + dz_high)
        full_range = range_high - dz_high
        if full_range <= 0:
            return 0
        return min(100, int(effective * 100 / full_range))

print("PHASE 3: CALIBRATED OUTPUT")
print("=" * 50)
print("Ctrl+C to stop")
print()

try:
    while True:
        x = map_calibrated(read_avg(joy_x), min_x, cx, max_x)
        y = map_calibrated(read_avg(joy_y), min_y, cy, max_y)
        z = map_calibrated(read_avg(joy_z), min_z, cz, max_z)

        dx = "R" if x > 15 else ("L" if x < -15 else "-")
        dy = "U" if y > 15 else ("D" if y < -15 else "-")
        dz = "CW" if z > 15 else ("CCW" if z < -15 else "--")

        print(f"X:{x:+4d} Y:{y:+4d} Z:{z:+4d}  [{dx:>2s} {dy:>2s} {dz:>3s}]")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nDone.")

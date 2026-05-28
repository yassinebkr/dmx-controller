# test_buttons.py — Resistor ladder button test for XIAO RP2040
# Wiring: A3 ← button ladder (22.2kΩ pull-up to 3.3V)
# Buttons wired: B1=0Ω, B2=220Ω, B3=560Ω, B4=1kΩ, B5=1.5kΩ, B6=2.7kΩ, B7=3.9kΩ, B8=6.8kΩ
#
# CircuitPython ADC: 16-bit (0–65535), NOT raw 12-bit
# The RP2040's 12-bit values get left-shifted to fill 16 bits

import board
import analogio
import time

adc = analogio.AnalogIn(board.A3)

# --- Phase 1: Raw value monitor ---
# Run this first to see actual ADC values for each button
# Press each button and note the readings — use those to set thresholds

print("=" * 40)
print("BUTTON ADC RAW MONITOR")
print("=" * 40)
print("Press each button and note the value.")
print("No press should read ~65535 (pulled up)")
print("Ctrl+C to move to Phase 2")
print()

try:
    while True:
        raw = adc.value
        voltage = raw * 3.3 / 65535
        print(f"ADC: {raw:5d}  |  Voltage: {voltage:.3f}V")
        time.sleep(0.3)
except KeyboardInterrupt:
    print("\n--- Moving to Phase 2 ---\n")

# --- Phase 2: Button detection with thresholds ---
# Expected 16-bit ADC values (22.2kΩ pull-up, 3.3V):
#   B1 (0Ω):    ~0       → threshold: 0–321
#   B2 (220Ω):  ~643     → threshold: 322–1127
#   B3 (560Ω):  ~1,612   → threshold: 1128–2218
#   B4 (1kΩ):   ~2,824   → threshold: 2219–3485
#   B5 (1.5kΩ): ~4,147   → threshold: 3486–5626
#   B6 (2.7kΩ): ~7,106   → threshold: 5627–8449
#   B7 (3.9kΩ): ~9,792   → threshold: 8450–12579
#   B8 (6.8kΩ): ~15,366  → threshold: 12580–40450
#   None:       ~65,535  → above 40450
#
# ADJUST these after seeing Phase 1 readings!

BUTTONS = [
    {"name": "B1 (0Ω)",    "low": 0,     "high": 321},
    {"name": "B2 (220Ω)",  "low": 322,   "high": 1127},
    {"name": "B3 (560Ω)",  "low": 1128,  "high": 2218},
    {"name": "B4 (1kΩ)",   "low": 2219,  "high": 3485},
    {"name": "B5 (1.5kΩ)", "low": 3486,  "high": 5626},
    {"name": "B6 (2.7kΩ)", "low": 5627,  "high": 8449},
    {"name": "B7 (3.9kΩ)", "low": 8450,  "high": 12579},
    {"name": "B8 (6.8kΩ)", "low": 12580, "high": 40450},
]

NO_PRESS_THRESHOLD = 40450

def read_button_averaged(samples=5, delay=0.005):
    """Read ADC with averaging to reduce noise."""
    total = 0
    for _ in range(samples):
        total += adc.value
        time.sleep(delay)
    return total // samples

def identify_button(value):
    """Match ADC value to a button."""
    for btn in BUTTONS:
        if btn["low"] <= value <= btn["high"]:
            return btn["name"]
    if value > NO_PRESS_THRESHOLD:
        return None  # no button pressed
    return "UNKNOWN"  # value in a gap — check wiring

print("BUTTON DETECTION (5-sample average)")
print("=" * 40)
print("Press buttons — names should appear")
print("Ctrl+C to stop")
print()

last_button = None
try:
    while True:
        avg = read_button_averaged()
        button = identify_button(avg)

        if button != last_button:
            if button is None:
                print(f"  Released  (ADC: {avg})")
            elif button == "UNKNOWN":
                print(f"  ⚠ UNKNOWN value: {avg} — check thresholds!")
            else:
                print(f"  ▶ {button} pressed  (ADC: {avg})")
            last_button = button

        time.sleep(0.05)
except KeyboardInterrupt:
    print("\nDone.")

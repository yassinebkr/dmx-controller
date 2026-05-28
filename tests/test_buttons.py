# test_buttons.py — Resistor ladder button test for XIAO RP2040
# Wiring: A3 ← button ladder (2.2kΩ pull-up to 3.3V)
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
# Expected 16-bit ADC values (2.2kΩ pull-up, 3.3V):
#   B1 (0Ω):    ~0       → threshold: 0–2978
#   B2 (220Ω):  ~5,957   → threshold: 2979–9626
#   B3 (560Ω):  ~13,296  → threshold: 9627–16887
#   B4 (1kΩ):   ~20,479  → threshold: 16888–23523
#   B5 (1.5kΩ): ~26,568  → threshold: 23524–31339
#   B6 (2.7kΩ): ~36,111  → threshold: 31340–39005
#   B7 (3.9kΩ): ~41,899  → threshold: 39006–45707
#   B8 (6.8kΩ): ~49,515  → threshold: 45708–57525
#   None:       ~65,535  → above 57525
#
# ADJUST these after seeing Phase 1 readings!

BUTTONS = [
    {"name": "B1 (0Ω)",    "low": 0,     "high": 2978},
    {"name": "B2 (220Ω)",  "low": 2979,  "high": 9626},
    {"name": "B3 (560Ω)",  "low": 9627,  "high": 16887},
    {"name": "B4 (1kΩ)",   "low": 16888, "high": 23523},
    {"name": "B5 (1.5kΩ)", "low": 23524, "high": 31339},
    {"name": "B6 (2.7kΩ)", "low": 31340, "high": 39005},
    {"name": "B7 (3.9kΩ)", "low": 39006, "high": 45707},
    {"name": "B8 (6.8kΩ)", "low": 45708, "high": 57525},
]

NO_PRESS_THRESHOLD = 57525

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

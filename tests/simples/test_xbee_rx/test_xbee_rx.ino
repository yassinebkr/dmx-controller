/*
 * XBee S1 — Simple Local Connection Test
 * ======================================
 * Tests if the XBee module is correctly wired and responding
 * by entering and exiting AT command mode.
 *
 * NO wireless transmission/reception — purely local UART check.
 *
 * Wiring:
 *   Pico TX -> XBee DIN
 *   Pico RX <- XBee DOUT
 *
 * Default pins: D2=RX, D3=TX
 * For XIAO RP2040: change to D7=RX, D6=TX
 */

#include <PicoSoftwareSerial.h>

// === CONFIGURATION ===
// Change these pins to match your board wiring
#define xiao_RX 2   // Connected to XBee DOUT (data FROM radio)
#define xiao_TX 0   // Connected to XBee DIN  (data TO radio)

SoftwareSerial xbee(xiao_TX, xiao_RX);

void setup() {
  Serial.begin(9600);
  while (!Serial) { ; }  // Wait for serial monitor on native-USB boards

  xbee.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  Serial.println(F("========================================"));
  Serial.println(F("  XBee Local Connection Test"));
  Serial.println(F("========================================"));
  Serial.println();

  // --- Step 1: Enter AT command mode ---
  Serial.println(F("[TEST] Entering AT command mode..."));

  delay(1100);              // Guard time: 1 s silence before
  xbee.print("+++");        // Command-mode sequence
  delay(1500);              // Guard time: 1 s silence after

  // Read response (wait up to 2 s)
  String resp = "";
  unsigned long t0 = millis();
  while (millis() - t0 < 2000) {
    while (xbee.available()) {
      resp += (char)xbee.read();
    }
  }
  resp.trim();

  // --- Step 2: Evaluate response ---
  if (resp.indexOf("OK") >= 0) {
    Serial.println(F("  >> OK received from XBee"));

    // Exit command mode cleanly
    Serial.println(F("[TEST] Exiting AT command mode..."));
    xbee.print("ATCN\r");
    delay(300);
    while (xbee.available()) xbee.read(); // flush OK response
 
    Serial.println();
    Serial.println(F("========================================"));
    Serial.println(F("  RESULT: XBee CONNECTED"));
    Serial.println(F("========================================"));

    // Success: LED stays ON
    digitalWrite(LED_BUILTIN, HIGH);
  }
  else {
    Serial.println(F("  >> No OK response"));
    if (resp.length() > 0) {
      Serial.print(F("  Raw response: ["));
      Serial.print(resp);
      Serial.println(F("]"));
    } else {
      Serial.println(F("  (empty response)"));
    }

    Serial.println();
    Serial.println(F("========================================"));
    Serial.println(F("  RESULT: XBee NOT DETECTED"));
    Serial.println(F("========================================"));
    Serial.println(F("Check:"));
    Serial.println(F("  - TX pin  -> XBee DIN"));
    Serial.println(F("  - RX pin  <- XBee DOUT"));
    Serial.println(F("  - 3.3 V and GND connected"));
    Serial.println(F("  - Baudrate is 9600"));

    // Failure: rapid LED blink
    for (int i = 0; i < 10; i++) {
      digitalWrite(LED_BUILTIN, HIGH);
      delay(100);
      digitalWrite(LED_BUILTIN, LOW);
      delay(100);
    }
  }
}

void loop() {
  // Test is one-shot in setup().
  // If connected, LED stays ON. If not, LED is OFF.
  delay(1000);
}

// Signs of life for an ESP32-S3 — the smallest thing that proves the board
// boots, the serial port is the one you are looking at, and one 8-pixel SK6812
// strip on GPIO 4 lights up.
//
// No WiFi, no OSC, no Garden State, no config headers. If this does not run,
// nothing else will either.

#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#include <esp_system.h>

#define STRIP_PIN 4
#define STRIP_PIXELS 8

// The DevKitC-1's own addressable LED: a sign of life that needs no wiring at
// all. GPIO 48 on v1.1 boards, GPIO 38 on v1.0. If it never lights, try the
// other one — it costs nothing to check.
#define ONBOARD_PIN 48

Adafruit_NeoPixel strip(STRIP_PIXELS, STRIP_PIN, NEO_GRBW + NEO_KHZ800);
Adafruit_NeoPixel onboard(1, ONBOARD_PIN, NEO_GRB + NEO_KHZ800);

const char *resetReason() {
  switch (esp_reset_reason()) {
    case ESP_RST_POWERON:  return "POWERON (normal — you plugged it in)";
    case ESP_RST_EXT:      return "EXT (reset button)";
    case ESP_RST_SW:       return "SW (software restart)";
    case ESP_RST_PANIC:    return "PANIC — the sketch crashed. Backtrace is above this line.";
    case ESP_RST_INT_WDT:  return "INT_WDT — interrupt watchdog";
    case ESP_RST_TASK_WDT: return "TASK_WDT — a task blocked too long";
    case ESP_RST_WDT:      return "WDT — watchdog";
    case ESP_RST_BROWNOUT: return "BROWNOUT — supply sagged. This is the LED-current one.";
    case ESP_RST_DEEPSLEEP:return "DEEPSLEEP";
    default:               return "UNKNOWN";
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);  // give the port time to come up before the banner

  Serial.println("\n\n=== signs of life ===");
  Serial.printf("reset reason: %s\n", resetReason());
  Serial.printf("strip: %d px on GPIO %d | onboard LED on GPIO %d\n",
                STRIP_PIXELS, STRIP_PIN, ONBOARD_PIN);

  onboard.begin();
  onboard.setBrightness(40);
  onboard.show();

  strip.begin();
  // 40/255 keeps 8 RGBW pixels near 100 mA total, so USB alone can run this.
  // Full white on 8 RGBW pixels is ~650 mA and will brown out a USB port —
  // which looks exactly like a boot loop.
  strip.setBrightness(40);
  strip.show();

  Serial.println("setup done — if the heartbeat stops, it crashed after this point");
}

void loop() {
  // Built with Color() rather than packed hex so the RGBW byte order cannot be
  // got wrong. The last one lights the W element alone: an RGB strip, or one
  // with the W leg unwired, stays dark for it instead of faking white.
  const uint32_t colors[] = {
      strip.Color(255, 0, 0, 0),
      strip.Color(0, 255, 0, 0),
      strip.Color(0, 0, 255, 0),
      strip.Color(0, 0, 0, 255),
  };
  static const char *names[] = {"red", "green", "blue", "white (W only)"};
  static int step = 0;

  const int index = step % 4;

  strip.fill(colors[index]);
  strip.show();

  onboard.setPixelColor(0, (step % 2) ? 0 : onboard.Color(0, 40, 0));
  onboard.show();

  Serial.printf("[%6lu ms] alive — strip %s\n", millis(), names[index]);

  ++step;
  delay(1000);
}

/*
  TreeHouse Branch Controller
  OpenRB-150 (SAMD21)

  Reads JSON-lines from USB serial (115200 baud):
      {"id": 1, "pos": 90.0}

  Drives the target Dynamixel servo to the requested position.

  Acknowledges each command:
      {"id": 1, "ok": true}

  Required libraries:
    - Dynamixel2Arduino
    - ArduinoJson (>= 6.x)
*/

#include <ArduinoJson.h>
#include <Dynamixel2Arduino.h>

// OpenRB-150 does not require a DIR control pin for Dynamixel.
#define DXL_SERIAL  Serial1
#define USB_SERIAL  Serial
const int DXL_DIR_PIN = -1;

Dynamixel2Arduino dxl(DXL_SERIAL, DXL_DIR_PIN);

const float DXL_PROTOCOL_VERSION = 2.0f;

#define MAX_BAUD 5
const int32_t BAUD_RATES[MAX_BAUD] = {57600, 115200, 1000000, 2000000, 3000000};

bool activeServos[DXL_BROADCAST_ID];

String inputBuffer = "";

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

void setup() {
  USB_SERIAL.begin(115200);
  // Brief wait so the USB-CDC host can enumerate; non-blocking after 2 s.
  unsigned long t = millis();
  while (!USB_SERIAL && (millis() - t) < 2000);

  scanForServos();
  USB_SERIAL.println("Branch controller ready");
}

// ---------------------------------------------------------------------------
// Main loop — non-blocking line accumulator
// ---------------------------------------------------------------------------

void loop() {
  while (USB_SERIAL.available()) {
    char c = (char)USB_SERIAL.read();
    if (c == '\n') {
      inputBuffer.trim();
      if (inputBuffer.length() > 0) {
        processLine(inputBuffer);
      }
      inputBuffer = "";
    } else if (c != '\r') {
      inputBuffer += c;
    }
  }
}

// ---------------------------------------------------------------------------
// Command handling
// ---------------------------------------------------------------------------

void processLine(const String& line) {
  StaticJsonDocument<64> doc;
  if (deserializeJson(doc, line) != DeserializationError::Ok) return;
  if (!doc.containsKey("id") || !doc.containsKey("pos")) return;

  int id = doc["id"];
  float pos = doc["pos"];
  setPosDeg((uint8_t)id, pos);

  StaticJsonDocument<32> ack;
  ack["id"] = id;
  ack["ok"] = true;
  serializeJson(ack, USB_SERIAL);
  USB_SERIAL.println();
}

// ---------------------------------------------------------------------------
// Servo helpers
// ---------------------------------------------------------------------------

void scanForServos() {
  memset(activeServos, false, sizeof(activeServos));
  dxl.setPortProtocolVersion(DXL_PROTOCOL_VERSION);

  USB_SERIAL.print("Scanning for Dynamixel servos (protocol ");
  USB_SERIAL.print(DXL_PROTOCOL_VERSION);
  USB_SERIAL.println(")...");

  for (uint8_t bi = 0; bi < MAX_BAUD; bi++) {
    USB_SERIAL.print("  baud ");
    USB_SERIAL.println(BAUD_RATES[bi]);
    dxl.begin(BAUD_RATES[bi]);
    bool foundAtThisBaud = false;

    for (uint8_t id = 0; id < DXL_BROADCAST_ID; id++) {
      if (!dxl.ping(id)) continue;
      activeServos[id] = true;
      foundAtThisBaud = true;

      USB_SERIAL.print("  found ID ");
      USB_SERIAL.print(id);
      USB_SERIAL.print(", model ");
      USB_SERIAL.println(dxl.getModelNumber(id));

      dxl.torqueOff(id);
      dxl.setOperatingMode(id, OP_EXTENDED_POSITION);
      dxl.torqueOn(id);
    }

    if (foundAtThisBaud) break;
  }
}

void setPosDeg(uint8_t id, float posDeg) {
  if (!activeServos[id]) return;
  dxl.writeControlTableItem(ControlTableItem::PROFILE_ACCELERATION, id, 1);
  dxl.writeControlTableItem(ControlTableItem::PROFILE_VELOCITY, id, 50);
  dxl.setGoalPosition(id, posDeg, UNIT_DEGREE);
}

/*
Follow Flower Controller
Scans for servos, then dispatches OSC messages targeted at those servos.
*/
#include <Dynamixel2Arduino.h>
#include <Ethernet.h>
#include <EthernetUdp.h>
#include <OSCMessage.h>
#include <SPI.h>

//OpenRB does not require the DIR control pin.
#define DXL_SERIAL Serial1
#define DEBUG_SERIAL Serial
const int DXL_DIR_PIN = -1;
Dynamixel2Arduino dxl(DXL_SERIAL, DXL_DIR_PIN);

const float DXL_PROTOCOL_VERSION = 2.0f;

#define MAX_BAUD  5
const int32_t baud[MAX_BAUD] = {57600, 115200, 1000000, 2000000, 3000000};

bool activeServos[DXL_BROADCAST_ID];

// --- Network config ---
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0x15, 0x01 };
IPAddress ip(192, 168, 1, 51);     // set for your LAN
const uint16_t localPort = 9000;   // the port you will SEND OSC TO

EthernetUDP Udp;
const int ETH_CS_PIN = 5;

// --- Diagnostic state ---
// Broadcast destination for 1Hz heartbeat. Layout tool + main.py listen here.
const IPAddress HB_BROADCAST(255, 255, 255, 255);
const uint16_t HB_PORT = 9100;
const unsigned long HB_INTERVAL_MS = 1000;

uint32_t pktRxCount   = 0;     // successfully parsed OSC messages
uint32_t pktDropCount = 0;     // packets that failed OSC parse
int      lastMotorId  = -1;    // last /cg/ff/rot motor id we acted on
float    lastMotorDeg = 0.0f;  // last /cg/ff/rot value we acted on
int32_t  scanBaud     = 0;     // Dynamixel bus baud rate selected at boot scan
uint8_t  foundCount   = 0;     // number of servos detected on bus
char     foundIdsCsv[256] = ""; // comma-separated list of detected servo IDs
unsigned long lastHbMs = 0;

void setup() {
  scanForServos();
  setUpOsc();
  lastHbMs = millis();
}

void loop() {
  // ---- diagnostic heartbeat (1Hz broadcast on HB_PORT) ----
  const unsigned long now = millis();
  if (now - lastHbMs >= HB_INTERVAL_MS) {
    lastHbMs = now;
    sendStatus(HB_BROADCAST, HB_PORT, "/cg/ff/hb");
  }

  int packetSize = Udp.parsePacket();
  if (packetSize <= 0) return;

  // Snapshot sender info before next parsePacket() overwrites it.
  IPAddress  remoteIp   = Udp.remoteIP();
  uint16_t   remotePort = Udp.remotePort();

  // Keep buffers small-ish; OpenRB-150 (SAMD21) has limited RAM.
  // 512 is usually fine for typical OSC messages.
  uint8_t buf[512];
  int len = Udp.read(buf, sizeof(buf));
  if (len <= 0) return;

  OSCMessage msg;
  msg.fill(buf, len);

  if (!msg.hasError()) {
    pktRxCount++;
    if (msg.fullMatch("/cg/ff/ping")) {
      sendStatus(remoteIp, remotePort, "/cg/ff/pong");
    } else {
      msg.route("/cg/ff/rot", onFlowerRot);
    }
  }
  else {
    pktDropCount++;
    OSCErrorCode e = msg.getError();
    DEBUG_SERIAL.print("OSC error: ");
    DEBUG_SERIAL.println((int)e);
  }
}

// Build + send the diagnostic OSC payload to (dest, port) under `addr`.
// Used for both periodic /cg/ff/hb broadcast and /cg/ff/pong unicast reply.
void sendStatus(IPAddress dest, uint16_t port, const char* addr) {
  OSCMessage out(addr);
  out.add((int32_t)mac[5]);          // ctrl_id from MAC last byte (unique per board)
  out.add((int32_t)scanBaud);
  out.add((int32_t)foundCount);
  out.add(foundIdsCsv);
  out.add((int32_t)pktRxCount);
  out.add((int32_t)pktDropCount);
  out.add((int32_t)lastMotorId);
  out.add(lastMotorDeg);

  Udp.beginPacket(dest, port);
  out.send(Udp);
  Udp.endPacket();
  out.empty();
}

void setUpOsc() {
  Ethernet.init(ETH_CS_PIN);

  // Start Ethernet (static IP; you can use DHCP with Ethernet.begin(mac) if you prefer)
  Ethernet.begin(mac, ip);

  Udp.begin(localPort);

  DEBUG_SERIAL.print("Listening for OSC on ");
  DEBUG_SERIAL.print(Ethernet.localIP());
  DEBUG_SERIAL.print(":");
  DEBUG_SERIAL.println(localPort);
}

void scanForServos() {
  uint8_t index = 0;
  uint8_t found_dynamixel = 0;

  // Use UART port of DYNAMIXEL Shield to debug.
  DEBUG_SERIAL.begin(115200);   //set debugging port baudrate to 115200bps
    
  // Set Port Protocol Version. This has to match with DYNAMIXEL protocol version.
  dxl.setPortProtocolVersion(DXL_PROTOCOL_VERSION);
  DEBUG_SERIAL.print("SCAN PROTOCOL ");
  DEBUG_SERIAL.println(DXL_PROTOCOL_VERSION);
  
  // Reset diagnostic state before scan.
  foundIdsCsv[0] = '\0';
  size_t csvLen = 0;

  for(index = 0; index < MAX_BAUD; index++) {
    bool useThisBaud = false;
    // Set Port baudrate.
    DEBUG_SERIAL.print("SCAN BAUDRATE ");
    DEBUG_SERIAL.println(baud[index]);
    dxl.begin(baud[index]);
    for(uint8_t id = 0; id < DXL_BROADCAST_ID; id++) {
      //iterate until all ID in each baudrate is scanned.
      const bool detected = dxl.ping(id);
      activeServos[id] = detected;

      if(detected) {
        DEBUG_SERIAL.print("ID : ");
        DEBUG_SERIAL.print(id);
        DEBUG_SERIAL.print(", Model Number: ");
        DEBUG_SERIAL.println(dxl.getModelNumber(id));
        found_dynamixel++;

        // Turn off torque when configuring items in EEPROM area
        dxl.torqueOff(id);
        dxl.setOperatingMode(id, OP_EXTENDED_POSITION);
        dxl.torqueOn(id);

        useThisBaud = true;

        // Append "id," to foundIdsCsv (bounded by buffer size).
        if (csvLen + 5 < sizeof(foundIdsCsv)) {
          csvLen += snprintf(foundIdsCsv + csvLen,
                             sizeof(foundIdsCsv) - csvLen,
                             "%u,", (unsigned)id);
        }
      }
    }

    if (useThisBaud) {
      scanBaud = baud[index];
      break;
    }
  }

  // Strip trailing comma if any.
  if (csvLen > 0 && foundIdsCsv[csvLen - 1] == ',') {
    foundIdsCsv[csvLen - 1] = '\0';
  }
  foundCount = found_dynamixel;

  DEBUG_SERIAL.print("Total ");
  DEBUG_SERIAL.print(found_dynamixel);
  DEBUG_SERIAL.println(" DYNAMIXEL(s) found!");
}

void onFlowerRot(OSCMessage& msg, int addressOffset) {
  const int id = msg.getInt(0);
  const float rot = msg.getFloat(1);
  lastMotorId  = id;
  lastMotorDeg = rot;
  setRotDeg(id, rot);
}

void setRotDeg(uint8_t id, float rotationDeg) {
  if (activeServos[id]) {
    dxl.writeControlTableItem(ControlTableItem::PROFILE_ACCELERATION, id, 1);
    dxl.writeControlTableItem(ControlTableItem::PROFILE_VELOCITY, id, 50);
    dxl.setGoalPosition(id, rotationDeg, UNIT_DEGREE);
  }
}

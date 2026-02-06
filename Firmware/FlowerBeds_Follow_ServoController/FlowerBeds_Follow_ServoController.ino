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
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0x15, 0x00 };
IPAddress ip(192, 168, 1, 50);     // set for your LAN
const uint16_t localPort = 9000;   // the port you will SEND OSC TO

EthernetUDP Udp;
const int ETH_CS_PIN = 5;

void setup() {
  scanForServos();
  setUpOsc();
}

void loop() {
  int packetSize = Udp.parsePacket();
  if (packetSize <= 0) return;

  // Keep buffers small-ish; OpenRB-150 (SAMD21) has limited RAM.
  // 512 is usually fine for typical OSC messages.
  uint8_t buf[512];
  int len = Udp.read(buf, sizeof(buf));
  if (len <= 0) return;

  OSCMessage msg;
  msg.fill(buf, len);

  if (!msg.hasError()) {
    msg.route("/cg/ff/rot", onFlowerRot);
  } 
  else {
    // Optional: print parse errors
    OSCErrorCode e = msg.getError();
    DEBUG_SERIAL.print("OSC error: ");
    DEBUG_SERIAL.println((int)e);
  }
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
      }
    }

    if (useThisBaud) {
      break;
    }
  }
  
  DEBUG_SERIAL.print("Total ");
  DEBUG_SERIAL.print(found_dynamixel);
  DEBUG_SERIAL.println(" DYNAMIXEL(s) found!");
}

void onFlowerRot(OSCMessage& msg, int addressOffset) {
  DEBUG_SERIAL.print("Rotating ");
  const int id = msg.getInt(0);
  DEBUG_SERIAL.print(id);
  DEBUG_SERIAL.print(", ");
  const float rot = msg.getFloat(1);
  DEBUG_SERIAL.println(rot);
  setRotDeg(id, rot);
}

void setRotDeg(uint8_t id, float rotationDeg) {
  if (activeServos[id]) {
    dxl.writeControlTableItem(ControlTableItem::PROFILE_ACCELERATION, id, 1);
    dxl.writeControlTableItem(ControlTableItem::PROFILE_VELOCITY, id, 50);
    dxl.setGoalPosition(id, rotationDeg, UNIT_DEGREE);
  }
}

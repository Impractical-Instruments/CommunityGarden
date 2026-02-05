/*
Follow Flower Controller
Scans for servos, then dispatches OSC messages targeted at those servos.
*/
#include <Dynamixel2Arduino.h>

//OpenRB does not require the DIR control pin.
#define DXL_SERIAL Serial1
#define DEBUG_SERIAL Serial
const int DXL_DIR_PIN = -1;
Dynamixel2Arduino dxl(DXL_SERIAL, DXL_DIR_PIN);

const float DXL_PROTOCOL_VERSION = 2.0f;

#define MAX_BAUD  5
const int32_t baud[MAX_BAUD] = {57600, 115200, 1000000, 2000000, 3000000};

bool activeServos[DXL_BROADCAST_ID];

void setup() {
  scanForServos();
}

void loop() {
  for (uint8_t i = 0; i < DXL_BROADCAST_ID; ++i) {
    setRotationDeg(i, 300);
  }

  delay(5000);

  for (uint8_t i = 0; i < DXL_BROADCAST_ID; ++i) {
    setRotationDeg(i, 400);
  }

  delay(5000);
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

void setRotationDeg(uint8_t id, float rotationDeg) {
  if (activeServos[id]) {
    dxl.writeControlTableItem(ControlTableItem::PROFILE_ACCELERATION, id, 1);
    dxl.writeControlTableItem(ControlTableItem::PROFILE_VELOCITY, id, 50);
    dxl.setGoalPosition(id, rotationDeg, UNIT_DEGREE);
  }
}

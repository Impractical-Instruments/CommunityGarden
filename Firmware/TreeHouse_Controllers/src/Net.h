// WiFi + UDP for a location controller.
//
// Everything here is non-blocking.  A controller that stalls waiting for an
// access point is a controller whose lights have stopped, which is the failure
// ADR-0020 exists to avoid: connection management runs alongside the animation
// loop, never in front of it.
#pragma once

#include <Arduino.h>

#include "OscRx.h"

namespace cg {

class Net {
 public:
  // `ip` is the static address from net_config.h (generated from network.json).
  void begin(const char* hostname, const uint8_t ip[4], uint16_t osc_port);

  // Call every loop.  Reconnects with backoff when the link drops.
  void poll(uint32_t now_ms);

  // Drains every queued UDP packet, passing each OSC message to `handler`.
  // Returns the number of packets read.
  int receive(osc::Handler handler, void* context);

  bool isConnected() const;
  IPAddress localIp() const;

 private:
  void connect(uint32_t now_ms);

  const char* hostname_ = "treehouse";
  uint16_t port_ = 9000;
  uint32_t next_attempt_ms_ = 0;
  uint32_t backoff_ms_ = 1000;
  bool udp_started_ = false;
  bool was_connected_ = false;
};

}  // namespace cg

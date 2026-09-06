// Garden State as it arrives on a TreeHouse location controller.
//
// The Pi is the only thing that knows how the Elements relate; a controller
// just receives the six Fabric fields (ADR-0007) and animates from them.  If
// the Pi goes quiet the last-known state is still here, which is what lets a
// controller keep running through a network drop (ADR-0020).
//
// Free of Arduino headers on purpose — this compiles and is tested on the host.

#pragma once

#include <cstdint>

#include "OscRx.h"

namespace cg {

enum class ShowMode { Active, Dim, Inactive };

struct GardenState {
  float flowerbeds_activity = 0.0f;
  float captcha_intensity = 0.0f;
  float pipes_activity = 0.0f;
  bool captcha_blowup = false;  // one-shot: true for exactly one consume()
  ShowMode show_mode = ShowMode::Active;
  float dim_level = 0.25f;      // level used while show_mode == Dim

  // Mirrors Coordinator.brightness in ShowControl/TreeHouse/coordinator.py.
  // Kept identical on both sides so a mode change looks the same on the Pi's
  // visualizer and on the wall.
  float masterBrightness() const;
};

// Default staleness horizon.  Two missed heartbeats at the Pi's 5 s interval.
constexpr uint32_t kDefaultStaleMs = 10000;

class GardenStateStore {
 public:
  explicit GardenStateStore(uint32_t stale_after_ms = kDefaultStaleMs)
      : stale_after_ms_(stale_after_ms) {}

  // Folds one received OSC message into the state.  Unrecognised addresses are
  // ignored and do not count as contact.
  void handle(const osc::Message& message, uint32_t now_ms);

  // Current state.  Clears the one-shot blowup flag, so call it once per frame.
  GardenState consume();

  // Peeks without clearing the blowup flag — for logging and tests.
  const GardenState& peek() const { return state_; }

  // True when nothing has been heard for longer than the staleness horizon,
  // including before the very first message.
  bool isStale(uint32_t now_ms) const;

  bool hasEverReceived() const { return has_received_; }
  uint32_t lastContactMs() const { return last_contact_ms_; }

 private:
  GardenState state_;
  uint32_t stale_after_ms_;
  uint32_t last_contact_ms_ = 0;
  bool has_received_ = false;
};

}  // namespace cg

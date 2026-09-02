#include "GardenState.h"

#include <cstring>

namespace cg {
namespace {

float clamp01(float value) {
  if (value < 0.0f) return 0.0f;
  if (value > 1.0f) return 1.0f;
  return value;
}

}  // namespace

float GardenState::masterBrightness() const {
  switch (show_mode) {
    case ShowMode::Inactive:
      return 0.0f;
    case ShowMode::Dim:
      return clamp01(dim_level);
    case ShowMode::Active:
    default:
      return 1.0f;
  }
}

void GardenStateStore::handle(const osc::Message& message, uint32_t now_ms) {
  bool recognised = true;

  if (message.is("/flowerbeds/activity")) {
    state_.flowerbeds_activity = clamp01(message.argFloat(0));
  } else if (message.is("/captcha/intensity")) {
    state_.captcha_intensity = clamp01(message.argFloat(0));
  } else if (message.is("/pipes/activity")) {
    state_.pipes_activity = clamp01(message.argFloat(0));
  } else if (message.is("/captcha/blowup")) {
    state_.captcha_blowup = true;
  } else if (message.is("/treehouse/brightness")) {
    state_.dim_level = clamp01(message.argFloat(0, state_.dim_level));
  } else if (message.is("/treehouse/mode")) {
    const char* mode = message.argString(0, "");
    if (std::strcmp(mode, "active") == 0) {
      state_.show_mode = ShowMode::Active;
    } else if (std::strcmp(mode, "dim") == 0) {
      state_.show_mode = ShowMode::Dim;
    } else if (std::strcmp(mode, "inactive") == 0) {
      state_.show_mode = ShowMode::Inactive;
    } else {
      recognised = false;  // unknown mode string: keep the mode we are in
    }
  } else {
    recognised = false;
  }

  if (recognised) {
    last_contact_ms_ = now_ms;
    has_received_ = true;
  }
}

GardenState GardenStateStore::consume() {
  GardenState snapshot = state_;
  state_.captcha_blowup = false;
  return snapshot;
}

bool GardenStateStore::isStale(uint32_t now_ms) const {
  if (!has_received_) return true;
  return (now_ms - last_contact_ms_) > stale_after_ms_;  // unsigned wrap is fine
}

}  // namespace cg

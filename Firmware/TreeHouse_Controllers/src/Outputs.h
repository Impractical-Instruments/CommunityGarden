// Hardware binding for the two kinds of channel a location can have:
// SK6812 RGBW strips (NeoPixelBus over RMT) and PWM MOSFET dimmers (LEDC).
//
// The animation engine in lib/Patterns knows nothing about either — it produces
// numbers, and this file is the only place those numbers touch a pin.
#pragma once

#include <Arduino.h>

#include "Patterns.h"

namespace cg {

// RMT channels available for LED output.  No location needs more than three.
constexpr size_t kMaxStrips = 3;

class StripOutput {
 public:
  // `slot` picks the RMT channel; pass 0, 1, 2 in order.
  bool begin(size_t slot, uint8_t pin, uint16_t pixel_count);
  void setPixel(uint16_t index, const Rgbw& color);
  void show();

 private:
  size_t slot_ = 0;
  uint16_t pixel_count_ = 0;
  bool ready_ = false;
};

class DimmerOutput {
 public:
  // 20 kHz keeps switching noise out of the audible band — these MOSFETs sit
  // inside a quiet room with a 12 V supply that will otherwise sing.
  static constexpr uint32_t kPwmFrequencyHz = 20000;
  static constexpr uint8_t kPwmResolutionBits = 13;

  bool begin(size_t slot, uint8_t pin);

  // `level` is 0–1 in perceptual terms; gamma is applied here so that half a
  // level looks like half the light rather than half the power.
  void write(float level);

 private:
  uint8_t pin_ = 0;
  uint8_t channel_ = 0;
  bool ready_ = false;
};

}  // namespace cg

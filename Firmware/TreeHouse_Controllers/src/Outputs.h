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
  // The LEDC timer can only run where frequency x 2^resolution fits inside its
  // clock, and on the ESP32-S3 the Arduino core feeds it from the 40 MHz XTAL
  // (SOC_LEDC_SUPPORT_XTAL_CLOCK).  So 13 bits caps out at 4.88 kHz:
  //
  //    4000 Hz x 8192 =  32.8 MHz — fits
  //   20000 Hz x 8192 = 163.8 MHz — does not, and the timer never starts
  //
  // Resolution wins here because dimmers fade filaments over seconds, where
  // coarse duty steps read as banding rather than as a smooth swell.  The cost
  // is that 4 kHz is inside the audible band: if the MOSFETs sing in a quiet
  // room, trade bits back for pitch — 10 bits buys 39 kHz.
  static constexpr uint32_t kPwmFrequencyHz = 4000;
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

// Hardware self-test: drives every channel from a fixed sequence with the
// network, Garden State and all the animation logic taken out of the picture.
//
// The point is to make a dark fixture mean exactly one thing.  If a strip stays
// dark under self-test, the fault is in the wiring, the level shifting, the
// power rail or the strip itself — there is nothing else left in the path.
//
// Compiled only when CG_SELFTEST is defined; see the -selftest environments in
// platformio.ini.
#pragma once

#include <Arduino.h>

#include "Outputs.h"
#include "Patterns.h"

namespace cg {

class SelfTest {
 public:
  // Level the strips are driven at.  Deliberately not full: a bench supply
  // should not have to deliver peak current to prove a strip works, and one of
  // these fixtures is bright enough to hurt.
  static constexpr float kLevel = 0.35f;

  void begin(const ChannelSpec* channels, size_t count, StripOutput* strips,
             DimmerOutput* dimmers, uint32_t now_ms);

  // Call once per frame.
  void update(uint32_t now_ms);

 private:
  enum class Phase { Red, Green, Blue, White, Walk, Dark };

  void advance(uint32_t now_ms);
  void render();
  const char* phaseName() const;

  const ChannelSpec* channels_ = nullptr;
  size_t count_ = 0;
  StripOutput* strips_ = nullptr;
  DimmerOutput* dimmers_ = nullptr;

  Phase phase_ = Phase::Red;
  uint32_t phase_start_ms_ = 0;
  uint16_t walk_index_ = 0;
  uint16_t max_pixels_ = 0;
};

}  // namespace cg

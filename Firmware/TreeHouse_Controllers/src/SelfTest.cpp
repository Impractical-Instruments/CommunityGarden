#include "SelfTest.h"

namespace cg {
namespace {

constexpr uint32_t kColorMs = 2000;
constexpr uint32_t kWalkStepMs = 150;
constexpr uint32_t kDarkMs = 1000;

uint8_t level8(float level) {
  const float scaled = level * 255.0f;
  if (scaled <= 0.0f) return 0;
  if (scaled >= 255.0f) return 255;
  return static_cast<uint8_t>(scaled + 0.5f);
}

}  // namespace

void SelfTest::begin(const ChannelSpec* channels, size_t count, StripOutput* strips,
                     DimmerOutput* dimmers, uint32_t now_ms) {
  channels_ = channels;
  count_ = count;
  strips_ = strips;
  dimmers_ = dimmers;
  phase_ = Phase::Red;
  phase_start_ms_ = now_ms;
  walk_index_ = 0;

  for (size_t i = 0; i < count_; ++i) {
    if (channels_[i].pixel_count > max_pixels_) max_pixels_ = channels_[i].pixel_count;
  }

  Serial.println("[selftest] network disabled — driving channels from the built-in sequence");
  Serial.printf("[selftest] red > green > blue > white > walk (%u px) > dark, repeating\n",
                max_pixels_);
}

void SelfTest::update(uint32_t now_ms) {
  const uint32_t elapsed = now_ms - phase_start_ms_;

  if (phase_ == Phase::Walk) {
    if (elapsed >= kWalkStepMs) {
      phase_start_ms_ = now_ms;
      ++walk_index_;
      if (walk_index_ >= max_pixels_) advance(now_ms);
    }
  } else {
    const uint32_t duration = (phase_ == Phase::Dark) ? kDarkMs : kColorMs;
    if (elapsed >= duration) advance(now_ms);
  }

  render();
}

void SelfTest::advance(uint32_t now_ms) {
  switch (phase_) {
    case Phase::Red: phase_ = Phase::Green; break;
    case Phase::Green: phase_ = Phase::Blue; break;
    case Phase::Blue: phase_ = Phase::White; break;
    case Phase::White: phase_ = Phase::Walk; walk_index_ = 0; break;
    case Phase::Walk: phase_ = Phase::Dark; break;
    case Phase::Dark: phase_ = Phase::Red; break;
  }
  phase_start_ms_ = now_ms;
  Serial.printf("[selftest] %s\n", phaseName());
}

const char* SelfTest::phaseName() const {
  switch (phase_) {
    case Phase::Red: return "red";
    case Phase::Green: return "green";
    case Phase::Blue: return "blue";
    case Phase::White: return "white (W element only)";
    case Phase::Walk: return "walk — one pixel at a time";
    case Phase::Dark: return "dark";
  }
  return "?";
}

void SelfTest::render() {
  const uint8_t on = level8(kLevel);

  // Full-saturation primaries, not the channel's configured base colour — this
  // is a test of the LEDs, not of how the location is meant to look.  The white
  // phase uses the W element alone, so a strip that is secretly RGB (or has the
  // W leg unwired) stays dark for it instead of faking white from R+G+B.
  Rgbw color;
  switch (phase_) {
    case Phase::Red: color = Rgbw{on, 0, 0, 0}; break;
    case Phase::Green: color = Rgbw{0, on, 0, 0}; break;
    case Phase::Blue: color = Rgbw{0, 0, on, 0}; break;
    case Phase::White: color = Rgbw{0, 0, 0, on}; break;
    case Phase::Walk: color = Rgbw{on, on, on, on}; break;
    case Phase::Dark: color = Rgbw{}; break;
  }

  for (size_t i = 0; i < count_; ++i) {
    const ChannelSpec& spec = channels_[i];

    if (spec.kind == ChannelKind::Strip) {
      for (uint16_t p = 0; p < spec.pixel_count; ++p) {
        const bool lit = (phase_ != Phase::Walk) || (p == walk_index_);
        strips_[i].setPixel(p, lit ? color : Rgbw{});
      }
      strips_[i].show();
      continue;
    }

    // Dimmers have no colour, so they climb in quarter steps across the four
    // colour phases instead.  Four visibly different brightnesses is also a
    // check on the gamma curve and the MOSFET's linearity.
    float level = 0.0f;
    switch (phase_) {
      case Phase::Red: level = 0.25f; break;
      case Phase::Green: level = 0.50f; break;
      case Phase::Blue: level = 0.75f; break;
      case Phase::White: level = 1.00f; break;
      case Phase::Walk: level = (walk_index_ % 2 == 0) ? 1.0f : 0.0f; break;  // blink
      case Phase::Dark: level = 0.0f; break;
    }
    dimmers_[i].write(level * spec.max_level);
  }
}

}  // namespace cg

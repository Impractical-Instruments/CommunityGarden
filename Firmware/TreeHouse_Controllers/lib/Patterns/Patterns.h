// The animation engine that runs on each location controller.
//
// One ChannelAnimator per physical channel.  Each holds a Signal Bag — the
// weighting pattern described in CONTEXT.md — that reduces Garden State to a
// single 0–1 drive value, smooths it, and feeds a pattern.
//
// No Arduino headers: this is arithmetic, and it is tested on the host.

#pragma once

#include <cstdint>

#include "GardenState.h"

namespace cg {

struct Rgbw {
  uint8_t r = 0;
  uint8_t g = 0;
  uint8_t b = 0;
  uint8_t w = 0;
};

enum class ChannelKind {
  Strip,   // SK6812 RGBW
  Dimmer,  // PWM MOSFET
};

enum class PatternId {
  Solid,         // flat base colour, scaled by drive
  Incandescent,  // warm per-pixel flicker, like filament bulbs
  Chase,         // lit head with a decaying tail, speed follows drive
  Mycelium,      // travelling wave along the strip
  Breathe,       // slow uniform swell — also the idle fallback
  Filament,      // dimmer: slow-slewing level with a hint of flicker
  Flash,         // dimmer: dark, with bursts that get more frequent under drive
};

// Per-channel weighting over Garden State.  Weights need not sum to 1 — the
// bag normalises by their total — so a channel can be retuned by editing one
// number without rebalancing the others.
struct Weights {
  float flowerbeds = 0.0f;
  float captcha = 0.0f;
  float pipes = 0.0f;
  float bias = 0.0f;  // floor added after normalising, before clamping

  float apply(const GardenState& state) const;
};

struct ChannelSpec {
  const char* name = "";
  ChannelKind kind = ChannelKind::Strip;
  uint8_t pin = 0;
  uint16_t pixel_count = 0;  // strips only
  Rgbw base;                 // strips: the channel's colour at full drive
  PatternId pattern = PatternId::Solid;
  Weights weights;
  float min_level = 0.0f;   // drive floor while the show is running
  float max_level = 1.0f;   // drive ceiling — caps a too-bright fixture
  float speed = 1.0f;       // pattern-specific rate multiplier
  float smoothing_s = 0.5f; // EMA time constant applied to drive
  float idle_level = 0.15f; // breathe amplitude when Garden State is stale
};

// How hard and how long the Blow-Up Reaction hits: spike to full, then decay
// exponentially back to the Garden-State-driven level (CONTEXT.md).
constexpr float kBlowUpDecayTau = 1.6f;

// Perceptual level (0-1) to PWM duty, gamma 2.2.  Lives here rather than with
// the LEDC code so it can be checked on the host.
uint32_t gammaDuty(float level, uint32_t max_duty);

class ChannelAnimator {
 public:
  void configure(const ChannelSpec& spec);

  // Advances by `dt` seconds.  `stale` comes from GardenStateStore::isStale()
  // and swaps the channel over to its idle behaviour.
  void update(float dt, const GardenState& state, bool stale);

  // Dimmer channels: the 0–1 level to write to PWM, master brightness applied.
  float level() const { return level_; }

  // Strip channels: the colour of pixel `index`, master brightness applied.
  Rgbw pixel(uint16_t index) const;

  const ChannelSpec& spec() const { return spec_; }
  float drive() const { return drive_; }

 private:
  float patternLevel(uint16_t index) const;

  ChannelSpec spec_;
  float time_s_ = 0.0f;
  float phase_ = 0.0f;   // 0–1, advances at a pattern-dependent rate
  float drive_ = 0.0f;   // smoothed Signal Bag output
  float blowup_ = 0.0f;  // decaying Blow-Up Reaction envelope
  float master_ = 1.0f;
  float level_ = 0.0f;
  bool stale_ = false;
};

}  // namespace cg

#include "Patterns.h"

#include <cmath>

namespace cg {
namespace {

constexpr float kTwoPi = 6.28318530718f;

float clamp01(float value) {
  if (value < 0.0f) return 0.0f;
  if (value > 1.0f) return 1.0f;
  return value;
}

uint8_t scale8(uint8_t value, float factor) {
  const float scaled = static_cast<float>(value) * factor;
  if (scaled <= 0.0f) return 0;
  if (scaled >= 255.0f) return 255;
  return static_cast<uint8_t>(scaled + 0.5f);
}

// Deterministic per-pixel offset, so flicker and phase differ pixel to pixel
// without storing any per-pixel state.  Cheap integer hash, then 0–1.
float pixelNoise(uint16_t index, uint32_t salt) {
  uint32_t h = index * 2654435761u + salt * 40503u;
  h ^= h >> 13;
  h *= 1274126177u;
  h ^= h >> 16;
  return static_cast<float>(h & 0xFFFFu) / 65535.0f;
}

// Two detuned sines: reads as an irregular flicker without a random source.
float flicker(float time_s, float offset) {
  const float a = std::sin((time_s * 4.7f + offset) * kTwoPi);
  const float b = std::sin((time_s * 11.3f + offset * 3.1f) * kTwoPi);
  return 0.5f + 0.25f * a + 0.25f * b;  // 0–1
}

// The idle fallback swaps a channel to Breathe when Garden State goes stale,
// because a stale controller can no longer trust its drive value.  A pattern
// that never reads drive has nothing to fall back from, so it keeps running
// as it is — see patternLevel().
bool usesDrive(PatternId pattern) { return pattern != PatternId::Flash; }

// Flash: four 250 ms bursts, evenly spaced, then a four-second pause.
constexpr float kFlashOnS = 0.25f;
constexpr float kFlashPeriodS = 0.5f;  // on, then an equal gap
constexpr int kFlashBursts = 4;
constexpr float kFlashPauseS = 4.0f;
constexpr float kFlashCycleS = kFlashBursts * kFlashPeriodS + kFlashPauseS;

}  // namespace

float Weights::apply(const GardenState& state) const {
  const float total = flowerbeds + captcha + pipes;
  float value = bias;
  if (total > 0.0f) {
    value += (flowerbeds * state.flowerbeds_activity + captcha * state.captcha_intensity +
              pipes * state.pipes_activity) /
             total;
  }
  return clamp01(value);
}

uint32_t gammaDuty(float level, uint32_t max_duty) {
  if (level <= 0.0f) return 0;
  if (level >= 1.0f) return max_duty;
  return static_cast<uint32_t>(std::pow(level, 2.2f) * static_cast<float>(max_duty) + 0.5f);
}

void ChannelAnimator::configure(const ChannelSpec& spec) {
  spec_ = spec;
  time_s_ = 0.0f;
  phase_ = 0.0f;
  drive_ = 0.0f;
  blowup_ = 0.0f;
  master_ = 1.0f;
  level_ = 0.0f;
  stale_ = false;
}

void ChannelAnimator::update(float dt, const GardenState& state, bool stale) {
  if (dt < 0.0f) dt = 0.0f;
  time_s_ += dt;
  stale_ = stale;
  master_ = state.masterBrightness();

  // Target drive: the Signal Bag while we have contact, a gentle idle swell
  // when we do not.  Either way it is smoothed, so the transition on a
  // recovered network is a fade rather than a jump.
  float target;
  if (stale) {
    target = spec_.idle_level;
  } else {
    const float bag = spec_.weights.apply(state);
    target = spec_.min_level + (spec_.max_level - spec_.min_level) * bag;
  }

  if (spec_.smoothing_s > 0.0f) {
    const float alpha = 1.0f - std::exp(-dt / spec_.smoothing_s);
    drive_ += (target - drive_) * alpha;
  } else {
    drive_ = target;
  }

  if (state.captcha_blowup && !stale) blowup_ = 1.0f;
  if (blowup_ > 0.0f) blowup_ *= std::exp(-dt / kBlowUpDecayTau);
  if (blowup_ < 0.001f) blowup_ = 0.0f;

  // Faster patterns under load; the +0.25 keeps things moving at zero drive.
  phase_ += dt * spec_.speed * (0.25f + drive_);
  phase_ -= std::floor(phase_);

  if (spec_.kind == ChannelKind::Dimmer) {
    level_ = clamp01(patternLevel(0)) * master_;
  }
}

float ChannelAnimator::patternLevel(uint16_t index) const {
  const PatternId pattern =
      (stale_ && usesDrive(spec_.pattern)) ? PatternId::Breathe : spec_.pattern;
  const float count = spec_.pixel_count > 0 ? static_cast<float>(spec_.pixel_count) : 1.0f;
  float value = 0.0f;

  switch (pattern) {
    case PatternId::Solid:
      value = drive_;
      break;

    case PatternId::Incandescent: {
      // Each pixel flickers around the drive level on its own offset, and
      // flickers harder when the drive is low — the way a dim filament does.
      const float offset = pixelNoise(index, 1u);
      const float depth = 0.10f + 0.15f * (1.0f - drive_);
      value = drive_ * (1.0f - depth * (1.0f - flicker(time_s_, offset)));
      break;
    }

    case PatternId::Chase: {
      // Distance from the head, wrapped, with an exponential tail.
      const float head = phase_ * count;
      float distance = static_cast<float>(index) - head;
      while (distance < 0.0f) distance += count;
      const float tail = 1.0f + 3.0f * (1.0f - drive_);  // tighter when busy
      value = drive_ * std::exp(-distance / tail);
      break;
    }

    case PatternId::Mycelium: {
      // A wave travelling along the run, riding on a floor that rises with
      // drive so the network never disappears entirely.
      const float waves = 1.5f;
      const float wave =
          0.5f + 0.5f * std::sin(kTwoPi * (static_cast<float>(index) / count * waves - phase_));
      value = drive_ * (0.35f + 0.65f * wave);
      break;
    }

    case PatternId::Breathe: {
      const float swell = 0.5f + 0.5f * std::sin(kTwoPi * phase_);
      const float amplitude = stale_ ? spec_.idle_level : drive_;
      value = amplitude * (0.35f + 0.65f * swell);
      break;
    }

    case PatternId::Filament: {
      // Mains-fed filaments never sit perfectly still; 6% wobble sells it.
      value = drive_ * (0.94f + 0.06f * flicker(time_s_, 0.37f));
      break;
    }

    case PatternId::Flash: {
      // A strobe burst on a fixed schedule: kFlashBursts on/off pairs, then a
      // long dark pause.  Binary — off, or the channel ceiling — so it reads
      // as a strobe and not as a lamp being faded up and down.  Timed off
      // time_s_ rather than phase_, so the burst length does not change with
      // drive; tying the burst rate to the Arc comes later.
      const float t = time_s_ - std::floor(time_s_ / kFlashCycleS) * kFlashCycleS;
      const float train = kFlashBursts * kFlashPeriodS;
      const bool lit = t < train && (t - std::floor(t / kFlashPeriodS) * kFlashPeriodS) < kFlashOnS;
      value = lit ? spec_.max_level : 0.0f;
      break;
    }
  }

  // The Blow-Up Reaction overrides whatever the pattern wanted, then decays
  // back into it.  Capped at the channel ceiling: max_level protects the
  // fixture, so nothing is allowed through it.
  const float spike = blowup_ * spec_.max_level;
  if (spike > value) value = spike;
  return clamp01(value);
}

Rgbw ChannelAnimator::pixel(uint16_t index) const {
  const float value = patternLevel(index) * master_;
  const Rgbw& base = spec_.base;
  return Rgbw{scale8(base.r, value), scale8(base.g, value), scale8(base.b, value),
              scale8(base.w, value)};
}

}  // namespace cg

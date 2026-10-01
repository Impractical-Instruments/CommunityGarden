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

uint8_t mix8(uint8_t from, uint8_t to, float t) {
  const float value =
      static_cast<float>(from) + (static_cast<float>(to) - static_cast<float>(from)) * t;
  if (value <= 0.0f) return 0;
  if (value >= 255.0f) return 255;
  return static_cast<uint8_t>(value + 0.5f);
}

Rgbw mixRgbw(const Rgbw& from, const Rgbw& to, float t) {
  return Rgbw{mix8(from.r, to.r, t), mix8(from.g, to.g, t), mix8(from.b, to.b, t),
              mix8(from.w, to.w, t)};
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
bool usesDrive(PatternId pattern) {
  return pattern != PatternId::Flash && pattern != PatternId::Weld;
}

// Fire and Weld are the only patterns that read ChannelSpec::base_hot.
// Everything else scales a single base colour, so a channel leaving base_hot at
// its default renders exactly as it did before the ramp existed.
bool usesRamp(PatternId pattern) {
  return pattern == PatternId::Fire || pattern == PatternId::Weld;
}

// FNV-1a over the channel name: a fixed per-channel seed, so two wandering
// channels on one controller do not walk in lockstep.
uint32_t nameSeed(const char* name) {
  uint32_t h = 2166136261u;
  for (const char* c = name; c != nullptr && *c != '\0'; ++c) {
    h ^= static_cast<uint8_t>(*c);
    h *= 16777619u;
  }
  return h;
}

float smoothstep(float t) { return t * t * (3.0f - 2.0f * t); }

// Wander: how long a leg takes is its distance times the full-sweep time,
// stretched or squeezed by up to 30% so the pace is as unsteady as the path.
// Short legs still take a few seconds — a stumble, not a twitch.
constexpr float kWanderSweepS = 60.0f;  // at speed 1.0
constexpr float kWanderPaceJitter = 0.3f;
constexpr float kWanderMinLegS = 4.0f;

// Weld: the arc is gone in a blink, the metal it heated takes seconds to cool.
// Each tap adds heat to the metal, so a long burst glows longer than one pop —
// but the metal never gets as bright as the arc, or the flash stops reading.
constexpr float kArcFlashTauS = 0.12f;
constexpr float kArcGlowTauS = 2.5f;
constexpr float kArcGlowPerTap = 0.2f;
constexpr float kArcGlowCeiling = 0.4f;

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
  rng_.reseed(nameSeed(spec.name));
  wander_from_ = 0.5f;
  wander_to_ = 0.5f;
  wander_t_ = 1.0f;
  wander_leg_s_ = 0.0f;
  flash_ = 0.0f;
  glow_ = 0.0f;
}

void ChannelAnimator::strike() {
  flash_ = 1.0f;
  glow_ += kArcGlowPerTap;
  if (glow_ > 1.0f) glow_ = 1.0f;
}

void ChannelAnimator::updateWander(float dt) {
  if (spec_.speed <= 0.0f) return;
  wander_t_ += wander_leg_s_ > 0.0f ? dt / wander_leg_s_ : 1.0f;
  if (wander_t_ < 1.0f) return;

  wander_from_ = wander_to_;
  wander_to_ = rng_.unit();
  const float distance = std::fabs(wander_to_ - wander_from_);
  const float pace = rng_.range(1.0f - kWanderPaceJitter, 1.0f + kWanderPaceJitter);
  wander_leg_s_ = distance * (kWanderSweepS / spec_.speed) * pace;
  if (wander_leg_s_ < kWanderMinLegS) wander_leg_s_ = kWanderMinLegS;
  wander_t_ = 0.0f;
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

  if (spec_.pattern == PatternId::Wander) updateWander(dt);
  if (flash_ > 0.0f) flash_ *= std::exp(-dt / kArcFlashTauS);
  if (glow_ > 0.0f) glow_ *= std::exp(-dt / kArcGlowTauS);

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

    case PatternId::Fire: {
      // Heat rather than brightness: hottest at the hearth and cooling toward
      // the tips, with licks drifting up the run and a per-pixel jitter over
      // the top.  The ember floor keeps the whole hearth alive, so a fire on
      // low drive reads as glowing coals and not as a strip with holes in it.
      const float height = static_cast<float>(index) / count;
      const float hearth = 1.0f - 0.5f * height;
      const float lick = 0.5f + 0.5f * std::sin(kTwoPi * (height * 2.0f - phase_));
      const float jitter = flicker(time_s_, pixelNoise(index, 7u));
      value = drive_ * hearth * (0.45f + 0.35f * lick + 0.20f * jitter);
      break;
    }

    case PatternId::Breathe: {
      // Configured, it swings between the floor and the drive — so min_level
      // is the darkest it ever gets.  As the stale fallback it has no drive to
      // trust and swells gently at idle_level instead.
      const float swell = 0.5f + 0.5f * std::sin(kTwoPi * phase_);
      if (stale_) {
        value = spec_.idle_level * (0.35f + 0.65f * swell);
      } else {
        value = spec_.min_level + (drive_ - spec_.min_level) * swell;
      }
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

    case PatternId::Wander: {
      const float t = wander_t_ < 1.0f ? wander_t_ : 1.0f;
      const float u = wander_from_ + (wander_to_ - wander_from_) * smoothstep(t);
      value = spec_.min_level + (drive_ - spec_.min_level) * u;
      break;
    }

    case PatternId::Weld: {
      // Each pixel sparkles on its own offset while the arc is lit — fast
      // enough (14–34 Hz) to read as crackle behind frosted acrylic — then the
      // whole run settles into a slow, uneven cooling glow.  Like Flash it is
      // drive-free and runs at the ceiling: the taps are the only input.
      const float sparkle = flicker(time_s_ * 3.0f, pixelNoise(index, 11u));
      const float arc = flash_ * (0.55f + 0.45f * sparkle);
      const float shimmer = flicker(time_s_ * 0.5f, pixelNoise(index, 13u));
      const float metal = kArcGlowCeiling * glow_ * (0.85f + 0.15f * shimmer);
      value = spec_.max_level * (arc > metal ? arc : metal);
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
  // A pixel's own level picks its colour off the ramp, so a fire is ember red
  // where it is dim and amber where it is hot.  Master brightness scales the
  // result but not the ramp position — dimming the show must not recolour it.
  // Keyed off the configured pattern rather than the effective one, so a stale
  // Fireplace breathes in fire colours instead of flat ember red.
  const float heat = patternLevel(index);
  const float value = heat * master_;
  const Rgbw base =
      usesRamp(spec_.pattern) ? mixRgbw(spec_.base, spec_.base_hot, heat) : spec_.base;
  return Rgbw{scale8(base.r, value), scale8(base.g, value), scale8(base.b, value),
              scale8(base.w, value)};
}

}  // namespace cg

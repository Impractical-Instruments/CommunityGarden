// A tiny deterministic PRNG for patterns that need to wander.
//
// xorshift32: four instructions a draw, no heap, no global state, and the same
// sequence on the host as on the S3 — so a seeded animator replays exactly in
// the native tests.  On hardware, seed from esp_random() to vary boot to boot.
//
// No Arduino headers: this is arithmetic, and it is tested on the host.

#pragma once

#include <cstdint>

namespace cg {

class Rng {
 public:
  explicit Rng(uint32_t seed = 1u) { reseed(seed); }

  // xorshift has one fixed point, zero, so a zero seed is remapped rather than
  // left to produce zeros forever.
  void reseed(uint32_t seed) { state_ = seed != 0u ? seed : 0x9E3779B9u; }

  uint32_t next() {
    state_ ^= state_ << 13;
    state_ ^= state_ >> 17;
    state_ ^= state_ << 5;
    return state_;
  }

  // Uniform in [0, 1).
  float unit() { return static_cast<float>(next() >> 8) / 16777216.0f; }

  // Uniform in [lo, hi).
  float range(float lo, float hi) { return lo + (hi - lo) * unit(); }

  // Uniform in [lo, hi], inclusive at both ends.
  uint32_t between(uint32_t lo, uint32_t hi) {
    if (hi <= lo) return lo;
    return lo + next() % (hi - lo + 1u);
  }

 private:
  uint32_t state_ = 1u;
};

}  // namespace cg

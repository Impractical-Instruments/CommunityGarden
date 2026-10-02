#include "Weld.h"

namespace cg {
namespace {

// Wrap-safe "has `now` reached `due`": millis() rolls over every 49.7 days,
// and a Garage left running that long must not stall for another 49.7.
bool reached(uint32_t now_ms, uint32_t due_ms) {
  return static_cast<int32_t>(now_ms - due_ms) >= 0;
}

}  // namespace

void Welder::configure(const WeldTiming& timing, uint32_t seed, uint32_t now_ms) {
  timing_ = timing;
  rng_.reseed(seed);
  bursts_left_ = 0;
  taps_left_ = 0;
  taps_fired_ = 0;
  next_ms_ = now_ms + rng_.between(timing_.session_gap_min_ms, timing_.session_gap_max_ms);
}

bool Welder::update(uint32_t now_ms) {
  if (!reached(now_ms, next_ms_)) return false;

  // Due, and nothing left to fire: the quiet gap just ended, so a new session
  // starts here and this call is its first tap.
  if (!inSession()) {
    bursts_left_ = rng_.between(timing_.bursts_min, timing_.bursts_max);
  }
  if (taps_left_ == 0) {
    taps_left_ = rng_.between(timing_.taps_min, timing_.taps_max);
    if (bursts_left_ > 0) --bursts_left_;
  }

  --taps_left_;
  ++taps_fired_;
  scheduleAfterTap(now_ms);
  return true;
}

void Welder::scheduleAfterTap(uint32_t now_ms) {
  uint32_t gap;
  if (taps_left_ > 0) {
    gap = rng_.between(timing_.tap_gap_min_ms, timing_.tap_gap_max_ms);
  } else if (bursts_left_ > 0) {
    gap = rng_.between(timing_.burst_gap_min_ms, timing_.burst_gap_max_ms);
  } else {
    gap = rng_.between(timing_.session_gap_min_ms, timing_.session_gap_max_ms);
  }
  next_ms_ = now_ms + gap;
}

}  // namespace cg

// The Garage welding schedule: when the arc light fires.
//
// The arc is a MOSFET dumping a charged capacitor through a very bright LED, so
// the firmware's only job is to say *when* — a short high pulse on the gate is
// one tap.  Taps come in bursts, bursts come in sessions, and the gaps at every
// level are random, because the effect only works if it surprises people:
//
//   session gap (quiet)  ->  burst  ->  burst gap  ->  burst  ...  ->  session gap
//                            tap tap tap
//
// Timing is integer milliseconds and the Welder is polled every loop(), not
// every frame: a 20 ms tap gap is barely more than one 16 ms frame, and frame
// jitter would smear the stutter that sells it.
//
// No Arduino headers: this is arithmetic, and it is tested on the host.

#pragma once

#include <cstdint>

#include "Rng.h"

namespace cg {

struct WeldTiming {
  uint32_t session_gap_min_ms = 8000;  // quiet between welding sessions
  uint32_t session_gap_max_ms = 25000;
  uint32_t bursts_min = 2;             // bursts in one session
  uint32_t bursts_max = 6;
  uint32_t burst_gap_min_ms = 1000;    // between bursts inside a session
  uint32_t burst_gap_max_ms = 5000;
  uint32_t taps_min = 1;               // taps in one burst
  uint32_t taps_max = 4;
  uint32_t tap_gap_min_ms = 20;        // between taps inside a burst; the
  uint32_t tap_gap_max_ms = 50;        // cap has to recharge in this window
  uint32_t pulse_ms = 5;               // gate high time for one tap
};

class Welder {
 public:
  // Starts with a quiet session gap, so a freshly booted Garage never opens on
  // a flash before anyone is looking.
  void configure(const WeldTiming& timing, uint32_t seed, uint32_t now_ms);

  // Call as often as possible.  Returns true exactly once per tap, on the
  // first call at or after it is due.  The next gap is measured from that call
  // rather than from the due time, so a late loop can never fire two taps
  // closer together than tap_gap_min_ms — the cap would not have recharged.
  bool update(uint32_t now_ms);

  uint32_t taps() const { return taps_fired_; }
  bool inSession() const { return bursts_left_ > 0 || taps_left_ > 0; }

 private:
  void scheduleAfterTap(uint32_t now_ms);

  WeldTiming timing_;
  Rng rng_;
  uint32_t next_ms_ = 0;
  uint32_t bursts_left_ = 0;  // bursts still to start in this session
  uint32_t taps_left_ = 0;    // taps still to fire in this burst
  uint32_t taps_fired_ = 0;
};

}  // namespace cg

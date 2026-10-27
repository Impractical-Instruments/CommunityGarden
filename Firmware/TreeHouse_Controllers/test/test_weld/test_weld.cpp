#include <unity.h>

#include <vector>

#include "Weld.h"

namespace {

// Tap times from polling a Welder every `step_ms` for `duration_ms`.
std::vector<uint32_t> tapTimes(uint32_t seed, uint32_t duration_ms, uint32_t step_ms = 1,
                               uint32_t start_ms = 0) {
  cg::Welder welder;
  welder.configure(cg::WeldTiming{}, seed, start_ms);
  std::vector<uint32_t> taps;
  for (uint32_t elapsed = 0; elapsed < duration_ms; elapsed += step_ms) {
    const uint32_t now = start_ms + elapsed;  // wraps, as millis() does
    if (welder.update(now)) taps.push_back(elapsed);
  }
  return taps;
}

enum class Gap { Tap, Burst, Session, Invalid };

// The three default ranges do not overlap, so every gap is exactly one kind.
Gap classify(uint32_t gap_ms) {
  const cg::WeldTiming t;
  if (gap_ms >= t.tap_gap_min_ms && gap_ms <= t.tap_gap_max_ms) return Gap::Tap;
  if (gap_ms >= t.burst_gap_min_ms && gap_ms <= t.burst_gap_max_ms) return Gap::Burst;
  if (gap_ms >= t.session_gap_min_ms && gap_ms <= t.session_gap_max_ms) return Gap::Session;
  return Gap::Invalid;
}

constexpr uint32_t kTenMinutesMs = 10u * 60u * 1000u;

}  // namespace

void setUp() {}
void tearDown() {}

void test_a_fresh_garage_starts_quiet() {
  const cg::WeldTiming t;
  for (uint32_t seed = 1; seed <= 20; ++seed) {
    const std::vector<uint32_t> taps = tapTimes(seed, 60000);
    TEST_ASSERT_FALSE(taps.empty());
    TEST_ASSERT_TRUE(taps.front() >= t.session_gap_min_ms);
    TEST_ASSERT_TRUE(taps.front() <= t.session_gap_max_ms);
  }
}

void test_every_gap_is_a_tap_burst_or_session_gap() {
  const std::vector<uint32_t> taps = tapTimes(7u, kTenMinutesMs);
  TEST_ASSERT_TRUE(taps.size() > 20);
  for (size_t i = 1; i < taps.size(); ++i) {
    TEST_ASSERT_TRUE(classify(taps[i] - taps[i - 1]) != Gap::Invalid);
  }
}

// Walks the gaps to recover the structure: taps per burst, bursts per session.
void test_bursts_and_sessions_vary_within_their_ranges() {
  const cg::WeldTiming t;
  const std::vector<uint32_t> taps = tapTimes(42u, 4u * kTenMinutesMs);

  std::vector<uint32_t> taps_per_burst;
  std::vector<uint32_t> bursts_per_session;
  uint32_t taps_in_burst = 1;
  uint32_t bursts_in_session = 1;
  for (size_t i = 1; i < taps.size(); ++i) {
    const Gap gap = classify(taps[i] - taps[i - 1]);
    if (gap == Gap::Tap) {
      ++taps_in_burst;
      continue;
    }
    taps_per_burst.push_back(taps_in_burst);
    taps_in_burst = 1;
    if (gap == Gap::Burst) {
      ++bursts_in_session;
    } else {
      bursts_per_session.push_back(bursts_in_session);
      bursts_in_session = 1;
    }
  }

  // The final burst and session may be cut off by the end of the run, so only
  // the closed ones are counted.
  TEST_ASSERT_TRUE(bursts_per_session.size() > 10);
  bool saw_single = false;
  bool saw_max_taps = false;
  for (uint32_t n : taps_per_burst) {
    TEST_ASSERT_TRUE(n >= t.taps_min && n <= t.taps_max);
    if (n == t.taps_min) saw_single = true;
    if (n == t.taps_max) saw_max_taps = true;
  }
  TEST_ASSERT_TRUE(saw_single);
  TEST_ASSERT_TRUE(saw_max_taps);

  uint32_t fewest = 1000;
  uint32_t most = 0;
  for (uint32_t n : bursts_per_session) {
    TEST_ASSERT_TRUE(n >= t.bursts_min && n <= t.bursts_max);
    if (n < fewest) fewest = n;
    if (n > most) most = n;
  }
  TEST_ASSERT_TRUE(most > fewest);
}

// A loop() that stalls must not fire a backlog of taps back to back: the cap
// needs its recharge window whatever the loop was doing.
void test_a_slow_loop_never_fires_faster_than_the_cap_recharges() {
  const cg::WeldTiming t;
  const std::vector<uint32_t> taps = tapTimes(3u, kTenMinutesMs, /*step_ms=*/70);
  TEST_ASSERT_TRUE(taps.size() > 20);
  for (size_t i = 1; i < taps.size(); ++i) {
    TEST_ASSERT_TRUE(taps[i] - taps[i - 1] >= t.tap_gap_min_ms);
  }
}

void test_same_seed_replays_and_different_seeds_do_not() {
  const std::vector<uint32_t> a = tapTimes(11u, kTenMinutesMs);
  const std::vector<uint32_t> b = tapTimes(11u, kTenMinutesMs);
  const std::vector<uint32_t> c = tapTimes(12u, kTenMinutesMs);
  TEST_ASSERT_TRUE(a == b);
  TEST_ASSERT_FALSE(a == c);
}

void test_keeps_welding_across_millis_rollover() {
  const uint32_t start = 0xFFFFFFFFu - 30000u;  // wraps 30 s in
  const std::vector<uint32_t> taps = tapTimes(5u, 3u * 60u * 1000u, 1, start);
  size_t after_wrap = 0;
  for (uint32_t elapsed : taps) {
    if (elapsed > 30000u) ++after_wrap;
  }
  TEST_ASSERT_TRUE(after_wrap > 5);
  for (size_t i = 1; i < taps.size(); ++i) {
    TEST_ASSERT_TRUE(classify(taps[i] - taps[i - 1]) != Gap::Invalid);
  }
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_a_fresh_garage_starts_quiet);
  RUN_TEST(test_every_gap_is_a_tap_burst_or_session_gap);
  RUN_TEST(test_bursts_and_sessions_vary_within_their_ranges);
  RUN_TEST(test_a_slow_loop_never_fires_faster_than_the_cap_recharges);
  RUN_TEST(test_same_seed_replays_and_different_seeds_do_not);
  RUN_TEST(test_keeps_welding_across_millis_rollover);
  return UNITY_END();
}

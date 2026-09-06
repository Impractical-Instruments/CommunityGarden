#include <unity.h>

#include "Patterns.h"

namespace {

cg::ChannelSpec dimmerSpec(cg::PatternId pattern) {
  cg::ChannelSpec spec;
  spec.name = "test";
  spec.kind = cg::ChannelKind::Dimmer;
  spec.pattern = pattern;
  spec.min_level = 0.0f;
  spec.max_level = 1.0f;
  spec.speed = 1.0f;
  spec.smoothing_s = 0.5f;
  spec.idle_level = 0.2f;
  return spec;
}

cg::ChannelSpec stripSpec(cg::PatternId pattern, uint16_t pixels) {
  cg::ChannelSpec spec = dimmerSpec(pattern);
  spec.kind = cg::ChannelKind::Strip;
  spec.pixel_count = pixels;
  spec.base = cg::Rgbw{0, 0, 0, 255};
  return spec;
}

cg::GardenState active(float flowerbeds = 0.0f) {
  cg::GardenState state;
  state.show_mode = cg::ShowMode::Active;
  state.flowerbeds_activity = flowerbeds;
  return state;
}

void run(cg::ChannelAnimator& animator, const cg::GardenState& state, float seconds,
         bool stale = false) {
  const float dt = 0.02f;
  for (float t = 0.0f; t < seconds; t += dt) animator.update(dt, state, stale);
}

}  // namespace

void setUp() {}
void tearDown() {}

void test_signal_bag_normalises_by_total_weight() {
  cg::GardenState state = active();
  state.flowerbeds_activity = 1.0f;
  state.captcha_intensity = 0.0f;

  cg::Weights even;
  even.flowerbeds = 1.0f;
  even.captcha = 1.0f;
  TEST_ASSERT_EQUAL_FLOAT(0.5f, even.apply(state));

  // Doubling both weights is the same balance, so the result must not move.
  cg::Weights doubled;
  doubled.flowerbeds = 2.0f;
  doubled.captcha = 2.0f;
  TEST_ASSERT_EQUAL_FLOAT(0.5f, doubled.apply(state));
}

void test_signal_bag_applies_bias_and_clamps() {
  cg::GardenState state = active();
  cg::Weights weights;
  weights.flowerbeds = 1.0f;
  weights.bias = 0.3f;

  state.flowerbeds_activity = 0.0f;
  TEST_ASSERT_EQUAL_FLOAT(0.3f, weights.apply(state));

  state.flowerbeds_activity = 1.0f;
  TEST_ASSERT_EQUAL_FLOAT(1.0f, weights.apply(state));  // 1.3 clamped
}

void test_drive_eases_toward_the_signal_bag() {
  cg::ChannelSpec spec = dimmerSpec(cg::PatternId::Solid);
  spec.weights.flowerbeds = 1.0f;
  cg::ChannelAnimator animator;
  animator.configure(spec);

  const cg::GardenState state = active(1.0f);
  animator.update(0.02f, state, false);
  TEST_ASSERT_TRUE(animator.drive() > 0.0f);
  TEST_ASSERT_TRUE(animator.drive() < 0.5f);  // eased, not jumped

  run(animator, state, 5.0f);
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 1.0f, animator.drive());
}

void test_inactive_mode_is_the_only_way_to_darkness() {
  cg::ChannelSpec spec = dimmerSpec(cg::PatternId::Filament);
  spec.weights.flowerbeds = 1.0f;
  cg::ChannelAnimator animator;
  animator.configure(spec);

  cg::GardenState state = active(1.0f);
  run(animator, state, 5.0f);
  TEST_ASSERT_TRUE(animator.level() > 0.5f);

  state.show_mode = cg::ShowMode::Inactive;
  animator.update(0.02f, state, false);
  TEST_ASSERT_EQUAL_FLOAT(0.0f, animator.level());
}

void test_dim_mode_scales_by_dim_level() {
  cg::ChannelSpec spec = dimmerSpec(cg::PatternId::Solid);
  spec.weights.bias = 1.0f;
  cg::ChannelAnimator animator;
  animator.configure(spec);

  cg::GardenState state = active();
  run(animator, state, 5.0f);
  const float full = animator.level();

  state.show_mode = cg::ShowMode::Dim;
  state.dim_level = 0.25f;
  animator.update(0.02f, state, false);
  TEST_ASSERT_FLOAT_WITHIN(0.02f, full * 0.25f, animator.level());
}

void test_stale_state_breathes_instead_of_going_dark() {
  cg::ChannelSpec spec = stripSpec(cg::PatternId::Solid, 4);
  spec.idle_level = 0.2f;
  cg::ChannelAnimator animator;
  animator.configure(spec);

  run(animator, active(), 8.0f, /*stale=*/true);

  uint8_t low = 255;
  uint8_t high = 0;
  for (int i = 0; i < 400; ++i) {  // a few breathe cycles
    animator.update(0.02f, active(), true);
    const uint8_t w = animator.pixel(0).w;
    if (w < low) low = w;
    if (w > high) high = w;
  }

  TEST_ASSERT_TRUE(high > 0);                      // never fully dark
  TEST_ASSERT_TRUE(high <= static_cast<uint8_t>(0.2f * 255.0f + 1));  // stays gentle
  TEST_ASSERT_TRUE(high > low);                    // and it is actually moving
}

void test_blowup_spikes_then_decays() {
  cg::ChannelSpec spec = dimmerSpec(cg::PatternId::Solid);
  cg::ChannelAnimator animator;
  animator.configure(spec);
  run(animator, active(), 2.0f);
  TEST_ASSERT_EQUAL_FLOAT(0.0f, animator.level());

  cg::GardenState blowup = active();
  blowup.captcha_blowup = true;
  animator.update(0.02f, blowup, false);
  TEST_ASSERT_TRUE(animator.level() > 0.9f);

  run(animator, active(), 6.0f);
  TEST_ASSERT_TRUE(animator.level() < 0.1f);
}

// A stale controller has no idea whether a Blow-Up is real, and the fixtures
// it would spike are bright enough that guessing wrong is unpleasant.
void test_blowup_is_ignored_while_stale() {
  cg::ChannelSpec spec = dimmerSpec(cg::PatternId::Filament);
  spec.idle_level = 0.0f;
  cg::ChannelAnimator animator;
  animator.configure(spec);

  cg::GardenState blowup = active();
  blowup.captcha_blowup = true;
  animator.update(0.02f, blowup, /*stale=*/true);
  TEST_ASSERT_EQUAL_FLOAT(0.0f, animator.level());
}

// The idle fallback exists to replace a drive that can no longer be trusted.
// Flash does not read drive, so a stale controller keeps strobing rather than
// going dark — which is what a location looks like when its Pi is missing.
void test_flash_keeps_strobing_while_stale() {
  cg::ChannelSpec spec = dimmerSpec(cg::PatternId::Flash);
  spec.max_level = 0.8f;
  spec.idle_level = 0.0f;  // as the Jess flash channel is configured
  cg::ChannelAnimator animator;
  animator.configure(spec);

  cg::GardenState blowup = active();
  blowup.captcha_blowup = true;

  int lit_ms = 0;
  for (int ms = 0; ms < 6000; ++ms) {
    animator.update(0.001f, blowup, /*stale=*/true);
    if (animator.level() > 0.0f) {
      ++lit_ms;
      // Still binary: a stale blowup must not spike it to full either.
      TEST_ASSERT_EQUAL_FLOAT(0.8f, animator.level());
    }
  }
  TEST_ASSERT_INT_WITHIN(8, 1000, lit_ms);
}

void test_flash_channel_strobes_in_bursts() {
  cg::ChannelSpec spec = dimmerSpec(cg::PatternId::Flash);
  spec.max_level = 0.8f;
  spec.weights.captcha = 1.0f;  // nothing drives it; the burst runs regardless
  cg::ChannelAnimator animator;
  animator.configure(spec);

  // Sample one 6 s cycle at 1 ms and count the on/off runs: four bursts of
  // 250 ms, then a 4 s pause.
  int edges = 0;
  int lit_ms = 0;
  bool lit = false;
  for (int ms = 0; ms < 6000; ++ms) {
    animator.update(0.001f, active(), false);
    const bool now_lit = animator.level() > 0.0f;
    if (now_lit) {
      ++lit_ms;
      TEST_ASSERT_EQUAL_FLOAT(0.8f, animator.level());  // binary, at the ceiling
    }
    if (now_lit != lit) ++edges;
    lit = now_lit;
  }
  TEST_ASSERT_EQUAL_INT(8, edges);       // four rising, four falling
  TEST_ASSERT_INT_WITHIN(8, 1000, lit_ms);  // 4 x 250 ms lit per cycle
}

void test_max_level_caps_even_the_blowup_spike() {
  cg::ChannelSpec spec = dimmerSpec(cg::PatternId::Flash);
  spec.max_level = 0.8f;
  spec.weights.captcha = 1.0f;
  cg::ChannelAnimator animator;
  animator.configure(spec);

  cg::GardenState state = active();
  state.captcha_intensity = 1.0f;
  state.captcha_blowup = true;

  float peak = 0.0f;
  for (int i = 0; i < 300; ++i) {
    animator.update(0.02f, state, false);
    state.captcha_blowup = false;
    if (animator.level() > peak) peak = animator.level();
  }
  TEST_ASSERT_TRUE(peak > 0.0f);
  TEST_ASSERT_TRUE(peak <= 0.8f);
}

void test_chase_lights_one_end_of_the_strip_at_a_time() {
  cg::ChannelSpec spec = stripSpec(cg::PatternId::Chase, 16);
  spec.weights.bias = 1.0f;
  cg::ChannelAnimator animator;
  animator.configure(spec);
  run(animator, active(), 3.0f);

  int lit = 0;
  for (uint16_t i = 0; i < 16; ++i) {
    if (animator.pixel(i).w > 8) ++lit;
  }
  TEST_ASSERT_TRUE(lit > 0);
  TEST_ASSERT_TRUE(lit < 16);  // a head and a tail, not the whole run
}

void test_gamma_duty_endpoints_and_monotonicity() {
  const uint32_t max_duty = 8191;
  TEST_ASSERT_EQUAL_UINT32(0, cg::gammaDuty(0.0f, max_duty));
  TEST_ASSERT_EQUAL_UINT32(max_duty, cg::gammaDuty(1.0f, max_duty));
  TEST_ASSERT_EQUAL_UINT32(0, cg::gammaDuty(-1.0f, max_duty));
  TEST_ASSERT_EQUAL_UINT32(max_duty, cg::gammaDuty(2.0f, max_duty));

  // Half perceptual level is well under half power — that is the point.
  TEST_ASSERT_TRUE(cg::gammaDuty(0.5f, max_duty) < max_duty / 3);

  uint32_t previous = 0;
  for (int i = 1; i <= 100; ++i) {
    const uint32_t duty = cg::gammaDuty(static_cast<float>(i) / 100.0f, max_duty);
    TEST_ASSERT_TRUE(duty >= previous);
    previous = duty;
  }
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_signal_bag_normalises_by_total_weight);
  RUN_TEST(test_signal_bag_applies_bias_and_clamps);
  RUN_TEST(test_drive_eases_toward_the_signal_bag);
  RUN_TEST(test_inactive_mode_is_the_only_way_to_darkness);
  RUN_TEST(test_dim_mode_scales_by_dim_level);
  RUN_TEST(test_stale_state_breathes_instead_of_going_dark);
  RUN_TEST(test_blowup_spikes_then_decays);
  RUN_TEST(test_blowup_is_ignored_while_stale);
  RUN_TEST(test_flash_keeps_strobing_while_stale);
  RUN_TEST(test_flash_channel_strobes_in_bursts);
  RUN_TEST(test_max_level_caps_even_the_blowup_spike);
  RUN_TEST(test_chase_lights_one_end_of_the_strip_at_a_time);
  RUN_TEST(test_gamma_duty_endpoints_and_monotonicity);
  return UNITY_END();
}

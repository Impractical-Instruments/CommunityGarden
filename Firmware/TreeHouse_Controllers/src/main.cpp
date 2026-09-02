// TreeHouse location controller — one ESP32-S3 per location (ADR-0020).
//
// Receives Garden State over UDP/OSC from the TreeHouse Pi and animates this
// location's channels locally.  The Pi never sends pixels, so the show keeps
// running through network drops; if the state goes stale the channels fall back
// to an idle breathe rather than freezing or going dark.
//
// Which location this binary is depends on the CG_TARGET_* macro set by the
// platformio.ini environment.  See src/targets/.
//
// Building with CG_SELFTEST replaces all of that with a fixed hardware test
// sequence and no networking at all — see src/SelfTest.h.

#include <Arduino.h>

#include "GardenState.h"
#include "Net.h"
#include "OscRx.h"
#include "Outputs.h"
#include "Patterns.h"
#include "targets/target.h"

#ifdef CG_SELFTEST
#include "SelfTest.h"
#endif

namespace {

constexpr uint32_t kFrameIntervalMs = 16;    // ~60 fps

cg::StripOutput g_strips[cg::target::kChannelCount];
cg::DimmerOutput g_dimmers[cg::target::kChannelCount];
uint32_t g_last_frame_ms = 0;

#ifdef CG_SELFTEST

cg::SelfTest g_selftest;

#else

constexpr uint32_t kHeartbeatMs = 5000;  // serial status line

cg::Net g_net;
cg::GardenStateStore g_state;
cg::ChannelAnimator g_animators[cg::target::kChannelCount];

uint32_t g_last_heartbeat_ms = 0;
uint32_t g_packets = 0;

void onOscMessage(const osc::Message& message, void* context) {
  auto* store = static_cast<cg::GardenStateStore*>(context);
  store->handle(message, millis());
}

void logHeartbeat(const cg::GardenState& state, bool stale) {
  const cg::GardenState& raw = g_state.peek();
  Serial.printf(
      "[%s] %s | fb %.2f cap %.2f pipes %.2f | master %.2f | %u pkt |",
      cg::target::kName, stale ? "STALE" : (g_net.isConnected() ? "ok" : "no-wifi"),
      raw.flowerbeds_activity, raw.captcha_intensity, raw.pipes_activity,
      state.masterBrightness(), g_packets);
  for (size_t i = 0; i < cg::target::kChannelCount; ++i) {
    Serial.printf(" %s=%.2f", g_animators[i].spec().name, g_animators[i].drive());
  }
  Serial.println();
}

#endif  // CG_SELFTEST

}  // namespace

void setup() {
  Serial.begin(115200);
  delay(200);  // let USB CDC enumerate so the banner is not lost
  Serial.printf("\n=== TreeHouse controller: %s (%u channels) ===\n", cg::target::kName,
                static_cast<unsigned>(cg::target::kChannelCount));

  size_t strip_slot = 0;
  size_t dimmer_slot = 0;
  for (size_t i = 0; i < cg::target::kChannelCount; ++i) {
    const cg::ChannelSpec& spec = cg::target::kChannels[i];
#ifndef CG_SELFTEST
    g_animators[i].configure(spec);
#endif

    if (spec.kind == cg::ChannelKind::Strip) {
      if (strip_slot >= cg::kMaxStrips) {
        Serial.printf("[setup] too many strips - %s not driven\n", spec.name);
        continue;
      }
      g_strips[i].begin(strip_slot++, spec.pin, spec.pixel_count);
      Serial.printf("[setup] strip  %-16s pin %2u  %u px\n", spec.name, spec.pin,
                    spec.pixel_count);
    } else {
      g_dimmers[i].begin(dimmer_slot++, spec.pin);
      Serial.printf("[setup] dimmer %-16s pin %2u\n", spec.name, spec.pin);
    }
  }

#ifdef CG_SELFTEST
  g_selftest.begin(cg::target::kChannels, cg::target::kChannelCount, g_strips, g_dimmers,
                   millis());
#else
  g_net.begin(cg::target::kName, cg::target::kIp, cg::target::kOscPort);
#endif

  g_last_frame_ms = millis();
}

void loop() {
  const uint32_t now = millis();

#ifdef CG_SELFTEST
  if (now - g_last_frame_ms >= kFrameIntervalMs) {
    g_last_frame_ms = now;
    g_selftest.update(now);
  }
  return;
#else
  g_net.poll(now);
  g_packets += static_cast<uint32_t>(g_net.receive(onOscMessage, &g_state));

  if (now - g_last_frame_ms < kFrameIntervalMs) return;
  const float dt = static_cast<float>(now - g_last_frame_ms) / 1000.0f;
  g_last_frame_ms = now;

  const bool stale = g_state.isStale(now);
  const cg::GardenState state = g_state.consume();

  for (size_t i = 0; i < cg::target::kChannelCount; ++i) {
    cg::ChannelAnimator& animator = g_animators[i];
    animator.update(dt, state, stale);

    if (animator.spec().kind == cg::ChannelKind::Strip) {
      for (uint16_t p = 0; p < animator.spec().pixel_count; ++p) {
        g_strips[i].setPixel(p, animator.pixel(p));
      }
      g_strips[i].show();
    } else {
      g_dimmers[i].write(animator.level());
    }
  }

  if (now - g_last_heartbeat_ms >= kHeartbeatMs) {
    g_last_heartbeat_ms = now;
    logHeartbeat(state, stale);
  }
#endif  // CG_SELFTEST
}

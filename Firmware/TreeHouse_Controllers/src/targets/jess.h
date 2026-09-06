// Jess — two SK6812 RGBW strips plus one MOSFET channel driving a very bright
// LED.
//
// The bright LED is a punctuation mark, not a light source: it is dark most of
// the time, strobes in short bursts, and goes full on for the Blow-Up
// Reaction.  Its ceiling is held below 1.0 because at full power, this close
// to the windows, it is genuinely painful to look at.
//
// For now the burst schedule is fixed (see kFlash* in Patterns.cpp) and does
// not follow the FundingCAPTCHA Arc; speed and smoothing are inert on it.
// Because it reads no drive, it also strobes on unchanged when the Pi is
// unreachable, rather than dropping to the idle breathe the strips fall back
// to.  A location with a dead Pi therefore still has a visible heartbeat.
#pragma once

namespace cg {
namespace target {

constexpr const char* kName = "Jess";
constexpr uint8_t kIp[4] = CG_IP_JESS;
constexpr uint16_t kOscPort = CG_OSC_PORT_JESS;

constexpr uint16_t kPixels = 20;  // per strip — provisional

constexpr ChannelSpec kChannels[] = {
    {
        .name = "Jess A",
        .kind = ChannelKind::Strip,
        .pin = 8,
        .pixel_count = 12,
        .base = Rgbw{255, 160, 60, 200},
        .pattern = PatternId::Incandescent,
        .weights = {.flowerbeds = 0.5f, .captcha = 0.3f, .pipes = 0.2f, .bias = 0.15f},
        .min_level = 0.18f,
        .max_level = 1.0f,
        .speed = 0.5f,
        .smoothing_s = 0.8f,
        .idle_level = 0.18f,
    },
    {
        .name = "Jess B",
        .kind = ChannelKind::Strip,
        .pin = 9,
        .pixel_count = 36,
        .base = Rgbw{60, 120, 255, 30},  // cool counterpoint to Jess A
        .pattern = PatternId::Mycelium,
        .weights = {.flowerbeds = 0.3f, .captcha = 0.4f, .pipes = 0.3f, .bias = 0.08f},
        .min_level = 0.12f,
        .max_level = 0.95f,
        .speed = 0.35f,
        .smoothing_s = 1.0f,
        .idle_level = 0.14f,
    },
    {
        .name = "Jess Flash",
        .kind = ChannelKind::Dimmer,
        .pin = 7,
        .pixel_count = 0,
        .base = Rgbw{},
        .pattern = PatternId::Flash,
        .weights = {.flowerbeds = 0.1f, .captcha = 0.8f, .pipes = 0.1f, .bias = 0.0f},
        .min_level = 0.0f,   // unused by the fixed burst; kept for when it drives again
        .max_level = 0.80f,
        .speed = 2.5f,
        .smoothing_s = 0.6f,
        .idle_level = 0.0f,  // unused: the burst is drive-free, so it survives a stale Pi
    },
};

constexpr size_t kChannelCount = sizeof(kChannels) / sizeof(kChannels[0]);

}  // namespace target
}  // namespace cg

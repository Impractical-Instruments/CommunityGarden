// Julia — one PWM MOSFET channel dimming a 12 V LED filament string.
//
// A soft glow on a very slow drunk walk between 40% and 80%, never dark: it
// eases toward a random level, then picks another, and a full sweep from one
// end to the other takes about a minute.
#pragma once

namespace cg {
namespace target {

constexpr const char* kName = "Julia";
constexpr uint8_t kIp[4] = CG_IP_JULIA;
constexpr uint16_t kOscPort = CG_OSC_PORT_JULIA;

constexpr ChannelSpec kChannels[] = {
    {
        .name = "Julia Filaments",
        .kind = ChannelKind::Dimmer,
        .pin = 7,
        .pixel_count = 0,
        .base = Rgbw{},  // unused on a dimmer channel
        .pattern = PatternId::Wander,
        .weights = {.flowerbeds = 0.5f, .captcha = 0.2f, .pipes = 0.3f, .bias = 0.20f},
        .min_level = 0.40f,  // the low end of the walk
        .max_level = 0.80f,  // the high end
        .speed = 1.0f,       // full sweep in 60 / speed s
        .smoothing_s = 2.0f,
        .idle_level = 0.20f,
    },
};

constexpr size_t kChannelCount = sizeof(kChannels) / sizeof(kChannels[0]);

}  // namespace target
}  // namespace cg

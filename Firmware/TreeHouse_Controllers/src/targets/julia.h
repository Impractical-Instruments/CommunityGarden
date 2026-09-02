// Julia — one PWM MOSFET channel dimming a 12 V LED filament string.
//
// Filaments have visible thermal lag, so the smoothing here is deliberately
// slow: chasing Garden State frame by frame would look wrong on this fixture
// even if the electronics could do it.
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
        .pattern = PatternId::Filament,
        .weights = {.flowerbeds = 0.5f, .captcha = 0.2f, .pipes = 0.3f, .bias = 0.20f},
        .min_level = 0.12f,  // never fully dark while the show is running
        .max_level = 1.0f,
        .speed = 0.2f,
        .smoothing_s = 2.0f,
        .idle_level = 0.20f,
    },
};

constexpr size_t kChannelCount = sizeof(kChannels) / sizeof(kChannels[0]);

}  // namespace target
}  // namespace cg

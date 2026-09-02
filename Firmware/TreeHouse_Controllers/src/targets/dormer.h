// Dormer — one PWM MOSFET channel on a 12 V LED circuit.
//
// The Dormer is the highest thing on the structure and reads from across the
// room, so it is capped below full: at 1.0 it flares in photographs and pulls
// attention off the windows.
#pragma once

namespace cg {
namespace target {

constexpr const char* kName = "Dormer";
constexpr uint8_t kIp[4] = CG_IP_DORMER;
constexpr uint16_t kOscPort = CG_OSC_PORT_DORMER;

constexpr ChannelSpec kChannels[] = {
    {
        .name = "Dormer",
        .kind = ChannelKind::Dimmer,
        .pin = 7,
        .pixel_count = 0,
        .base = Rgbw{},
        .pattern = PatternId::Filament,
        .weights = {.flowerbeds = 0.4f, .captcha = 0.4f, .pipes = 0.2f, .bias = 0.25f},
        .min_level = 0.20f,
        .max_level = 0.80f,
        .speed = 0.15f,
        .smoothing_s = 1.5f,
        .idle_level = 0.25f,
    },
};

constexpr size_t kChannelCount = sizeof(kChannels) / sizeof(kChannels[0]);

}  // namespace target
}  // namespace cg

// Dormer — one PWM MOSFET channel on a 12 V LED circuit.
//
// A soft glow breathing slowly between 40% and 80%, never dark.  The Dormer is
// the highest thing on the structure and reads from across the room, so it is
// capped below full: at 1.0 it flares in photographs and pulls attention off
// the windows.
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
        .pattern = PatternId::Breathe,
        .weights = {.flowerbeds = 0.4f, .captcha = 0.4f, .pipes = 0.2f, .bias = 0.25f},
        .min_level = 0.40f,  // bottom of the breath
        .max_level = 0.80f,  // top of the breath
        // Phase runs at speed x (0.25 + drive), and drive sits at max_level,
        // so 0.076 x 1.05 is one breath every 12.5 s.
        .speed = 0.076f,
        .smoothing_s = 1.5f,
        .idle_level = 0.25f,
    },
};

constexpr size_t kChannelCount = sizeof(kChannels) / sizeof(kChannels[0]);

}  // namespace target
}  // namespace cg

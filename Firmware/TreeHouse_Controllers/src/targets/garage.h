// Garage — the welding effect.  A capacitor-discharge arc flash plus a run of
// SK6812 RGBW pixels behind the same frosted acrylic windows.
//
// Not real welding: mad-scientist welding.  The arc is dark for long, random
// stretches and then goes off in stuttering bursts.  The pixels are what the
// arc leaves behind: a crackling violet-white flash under each tap, then
// metal cooling through orange back to dark.  When the arc is lit it washes
// the pixels out, which is fine — they are for the moments in between.
//
// The arc channel is not dimmed.  Its MOSFET dumps a charged cap, so one tap
// is just a short high pulse on the gate and the cap decides how long the
// flash is.  The cap recharges fast enough for taps 20-50 ms apart.
#pragma once

namespace cg {
namespace target {

constexpr const char* kName = "Garage";
constexpr uint8_t kIp[4] = CG_IP_GARAGE;
constexpr uint16_t kOscPort = CG_OSC_PORT_GARAGE;

// Placeholders — set these to the real wiring on the bench.  Avoid the
// strapping pins (0/3/45/46), the USB pair (19/20) and the flash/PSRAM range.
constexpr uint8_t kArcPin = 6;
constexpr uint8_t kGlowPin = 8;
constexpr uint16_t kGlowPixels = 16;

constexpr ChannelSpec kChannels[] = {
    {
        .name = "Arc",
        .kind = ChannelKind::Trigger,
        .pin = kArcPin,
        .weld =
            {
                .session_gap_min_ms = 8000,  // quiet between welding sessions
                .session_gap_max_ms = 25000,
                .bursts_min = 2,             // bursts per session
                .bursts_max = 6,
                .burst_gap_min_ms = 1000,    // between bursts in a session
                .burst_gap_max_ms = 5000,
                .taps_min = 1,               // taps per burst
                .taps_max = 4,
                .tap_gap_min_ms = 20,        // the cap's recharge window
                .tap_gap_max_ms = 50,
                .pulse_ms = 15,              // gate high time; must stay well
                                             // under tap_gap_min_ms
            },
    },
    {
        .name = "Glow",
        .kind = ChannelKind::Strip,
        .pin = kGlowPin,
        .pixel_count = kGlowPixels,
        .base = Rgbw{255, 60, 0, 0},           // metal cooling — orange to dark
        .base_hot = Rgbw{140, 120, 255, 180},  // the arc — violet-white
        .pattern = PatternId::Weld,
        .max_level = 1.0f,
    },
};

static_assert(kChannels[0].weld.pulse_ms < kChannels[0].weld.tap_gap_min_ms,
              "the arc pulse must end before the next tap can start");

constexpr size_t kChannelCount = sizeof(kChannels) / sizeof(kChannels[0]);

}  // namespace target
}  // namespace cg

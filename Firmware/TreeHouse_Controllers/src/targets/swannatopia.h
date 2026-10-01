// Swannatopia — three SK6812 RGBW strips: the fireplace, and the two overhead
// lights over the dining and living rooms.  The overheads are the same warm
// incandescent on purpose, so they share one spec and differ only in wiring.
//
// LED counts are a placeholder until the strips are cut and counted; change
// kPixels and reflash.  Data pins avoid the ESP32-S3 strapping pins (0/3/45/46),
// the USB pair (19/20) and the flash/PSRAM range.
#pragma once

namespace cg {
namespace target {

constexpr const char* kName = "Swannatopia";
constexpr uint8_t kIp[4] = CG_IP_SWANNATOPIA;
constexpr uint16_t kOscPort = CG_OSC_PORT_SWANNATOPIA;

constexpr uint16_t kPixels = 8;  // per strip — provisional

constexpr ChannelSpec overhead(const char* name, uint8_t pin, uint16_t pixel_count) {
  return ChannelSpec{
      .name = name,
      .kind = ChannelKind::Strip,
      .pin = pin,
      .pixel_count = pixel_count,
      .base = Rgbw{255, 180, 80, 255},  // warm white with an amber cast
      .pattern = PatternId::Incandescent,
      .weights = {.flowerbeds = 0.6f, .captcha = 0.2f, .pipes = 0.2f, .bias = 0.15f},
      .min_level = 0.20f,
      .max_level = 1.0f,
      .speed = 0.5f,
      .smoothing_s = 0.8f,
      .idle_level = 0.18f,
  };
}

constexpr ChannelSpec kChannels[] = {
    overhead("Overhead", 11, kPixels),
    {
        .name = "Fireplace",
        .kind = ChannelKind::Strip,
        .pin = 12,
        .pixel_count = kPixels,
        .base = Rgbw{140, 20, 0, 0},         // deep red ember — the dim end of the fire
        .base_hot = Rgbw{255, 150, 20, 40},  // amber-white, a touch of white in the tips
        .pattern = PatternId::Fire,
        .weights = {.flowerbeds = 0.2f, .captcha = 0.3f, .pipes = 0.5f, .bias = 0.05f},
        .min_level = 0.25f,    // the hearth is never out while the show is running
        .max_level = 1.0f,
        .speed = 0.6f,         // licks drift up the strip; they do not race
        .smoothing_s = 0.35f,  // still short, so a Blow-Up flares the fire
        .idle_level = 0.12f,
    },
    overhead("Chandelier", 13, 46),
};

constexpr size_t kChannelCount = sizeof(kChannels) / sizeof(kChannels[0]);

}  // namespace target
}  // namespace cg

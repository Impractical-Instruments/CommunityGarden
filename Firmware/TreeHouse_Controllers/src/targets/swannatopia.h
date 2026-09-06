// Swannatopia — three SK6812 RGBW strips.
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

constexpr ChannelSpec kChannels[] = {
    {
        .name = "Overhead",
        .kind = ChannelKind::Strip,
        .pin = 11,
        .pixel_count = kPixels,
        .base = Rgbw{255, 180, 80, 255},  // warm white with an amber cast
        .pattern = PatternId::Incandescent,
        .weights = {.flowerbeds = 0.6f, .captcha = 0.2f, .pipes = 0.2f, .bias = 0.15f},
        .min_level = 0.20f,
        .max_level = 1.0f,
        .speed = 0.5f,
        .smoothing_s = 0.8f,
        .idle_level = 0.18f,
    },
    {
        .name = "Fireplace",
        .kind = ChannelKind::Strip,
        .pin = 12,
        .pixel_count = kPixels,
        .base = Rgbw{180, 40, 255, 0},  // violet, no white — reads as colour
        .pattern = PatternId::Chase,
        .weights = {.flowerbeds = 0.2f, .captcha = 0.3f, .pipes = 0.5f, .bias = 0.05f},
        .min_level = 0.10f,
        .max_level = 1.0f,
        .speed = 1.4f,
        .smoothing_s = 0.35f,
        .idle_level = 0.12f,
    },
    {
        .name = "Chandelier",
        .kind = ChannelKind::Strip,
        .pin = 13,
        .pixel_count = 46,
        .base = Rgbw{80, 255, 120, 40},  // green with a touch of white
        .pattern = PatternId::Incandescent,
        .weights = {.flowerbeds = 0.5f, .captcha = 0.2f, .pipes = 0.3f, .bias = 0.10f},
        .min_level = 0.15f,
        .max_level = 0.95f,
        .speed = 0.28f,
        .smoothing_s = 1.2f,
        .idle_level = 0.15f,
    },
};

constexpr size_t kChannelCount = sizeof(kChannels) / sizeof(kChannels[0]);

}  // namespace target
}  // namespace cg

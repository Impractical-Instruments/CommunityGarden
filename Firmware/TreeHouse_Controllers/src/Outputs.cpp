#include "Outputs.h"

#include <NeoPixelBus.h>

namespace cg {
namespace {

// One concrete bus type per RMT channel: NeoPixelBus picks the peripheral at
// compile time, so the channel cannot be a runtime value.
using Bus0 = NeoPixelBus<NeoGrbwFeature, NeoEsp32Rmt0Sk6812Method>;
using Bus1 = NeoPixelBus<NeoGrbwFeature, NeoEsp32Rmt1Sk6812Method>;
using Bus2 = NeoPixelBus<NeoGrbwFeature, NeoEsp32Rmt2Sk6812Method>;

Bus0* g_bus0 = nullptr;
Bus1* g_bus1 = nullptr;
Bus2* g_bus2 = nullptr;

}  // namespace

bool StripOutput::begin(size_t slot, uint8_t pin, uint16_t pixel_count) {
  slot_ = slot;
  pixel_count_ = pixel_count;
  ready_ = true;

  switch (slot) {
    case 0:
      g_bus0 = new Bus0(pixel_count, pin);
      g_bus0->Begin();
      g_bus0->Show();
      break;
    case 1:
      g_bus1 = new Bus1(pixel_count, pin);
      g_bus1->Begin();
      g_bus1->Show();
      break;
    case 2:
      g_bus2 = new Bus2(pixel_count, pin);
      g_bus2->Begin();
      g_bus2->Show();
      break;
    default:
      Serial.printf("[out] no RMT slot for strip on pin %u\n", pin);
      ready_ = false;
      break;
  }
  return ready_;
}

void StripOutput::setPixel(uint16_t index, const Rgbw& color) {
  if (!ready_ || index >= pixel_count_) return;
  const RgbwColor value(color.r, color.g, color.b, color.w);
  switch (slot_) {
    case 0: g_bus0->SetPixelColor(index, value); break;
    case 1: g_bus1->SetPixelColor(index, value); break;
    case 2: g_bus2->SetPixelColor(index, value); break;
    default: break;
  }
}

void StripOutput::show() {
  if (!ready_) return;
  // CanShow() is false while the previous frame is still clocking out; skipping
  // is correct — the next frame is 16 ms away and carries newer data anyway.
  switch (slot_) {
    case 0: if (g_bus0->CanShow()) g_bus0->Show(); break;
    case 1: if (g_bus1->CanShow()) g_bus1->Show(); break;
    case 2: if (g_bus2->CanShow()) g_bus2->Show(); break;
    default: break;
  }
}

bool DimmerOutput::begin(size_t slot, uint8_t pin) {
  pin_ = pin;
  channel_ = static_cast<uint8_t>(slot);

#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ready_ = ledcAttach(pin_, kPwmFrequencyHz, kPwmResolutionBits);
#else
  ledcSetup(channel_, kPwmFrequencyHz, kPwmResolutionBits);
  ledcAttachPin(pin_, channel_);
  ready_ = true;
#endif

  if (!ready_) Serial.printf("[out] LEDC attach failed on pin %u\n", pin_);
  write(0.0f);
  return ready_;
}

void DimmerOutput::write(float level) {
  if (!ready_) return;
  const uint32_t max_duty = (1u << kPwmResolutionBits) - 1u;
  const uint32_t duty = gammaDuty(level, max_duty);
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(pin_, duty);
#else
  ledcWrite(channel_, duty);
#endif
}

}  // namespace cg

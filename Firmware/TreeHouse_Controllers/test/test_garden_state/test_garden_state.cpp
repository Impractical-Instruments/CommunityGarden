#include <unity.h>

#include <cstring>
#include <string>

#include "GardenState.h"

namespace {

void pushString(std::string& packet, const char* text) {
  packet += text;
  do {
    packet += '\0';
  } while (packet.size() % 4 != 0);
}

void pushFloat(std::string& packet, float value) {
  uint32_t raw;
  std::memcpy(&raw, &value, sizeof(raw));
  packet += static_cast<char>((raw >> 24) & 0xFF);
  packet += static_cast<char>((raw >> 16) & 0xFF);
  packet += static_cast<char>((raw >> 8) & 0xFF);
  packet += static_cast<char>(raw & 0xFF);
}

// Feeds one message into the store, the way Net::receive would.
void send(cg::GardenStateStore& store, uint32_t now_ms, const char* address,
          const char* typetag, float number, const char* text) {
  std::string packet;
  pushString(packet, address);
  pushString(packet, typetag);
  if (std::strcmp(typetag, ",f") == 0) pushFloat(packet, number);
  if (std::strcmp(typetag, ",s") == 0) pushString(packet, text);

  osc::Message message;
  TEST_ASSERT_TRUE(osc::parseMessage(reinterpret_cast<const uint8_t*>(packet.data()),
                                     packet.size(), message));
  store.handle(message, now_ms);
}

void sendFloat(cg::GardenStateStore& store, uint32_t now_ms, const char* address, float value) {
  send(store, now_ms, address, ",f", value, "");
}

void sendString(cg::GardenStateStore& store, uint32_t now_ms, const char* address,
                const char* value) {
  send(store, now_ms, address, ",s", 0.0f, value);
}

void sendBare(cg::GardenStateStore& store, uint32_t now_ms, const char* address) {
  send(store, now_ms, address, ",", 0.0f, "");
}

}  // namespace

void setUp() {}
void tearDown() {}

void test_folds_fabric_addresses_into_state() {
  cg::GardenStateStore store;
  sendFloat(store, 100, "/flowerbeds/activity", 0.4f);
  sendFloat(store, 100, "/captcha/intensity", 0.7f);
  sendFloat(store, 100, "/pipes/activity", 0.2f);

  const cg::GardenState& state = store.peek();
  TEST_ASSERT_EQUAL_FLOAT(0.4f, state.flowerbeds_activity);
  TEST_ASSERT_EQUAL_FLOAT(0.7f, state.captcha_intensity);
  TEST_ASSERT_EQUAL_FLOAT(0.2f, state.pipes_activity);
}

void test_clamps_out_of_range_values() {
  cg::GardenStateStore store;
  sendFloat(store, 100, "/flowerbeds/activity", 4.2f);
  sendFloat(store, 100, "/pipes/activity", -3.0f);

  TEST_ASSERT_EQUAL_FLOAT(1.0f, store.peek().flowerbeds_activity);
  TEST_ASSERT_EQUAL_FLOAT(0.0f, store.peek().pipes_activity);
}

void test_blowup_is_one_shot() {
  cg::GardenStateStore store;
  sendBare(store, 100, "/captcha/blowup");

  TEST_ASSERT_TRUE(store.consume().captcha_blowup);
  TEST_ASSERT_FALSE(store.consume().captcha_blowup);
}

void test_mode_strings_and_master_brightness() {
  cg::GardenStateStore store;
  TEST_ASSERT_EQUAL_FLOAT(1.0f, store.peek().masterBrightness());

  sendString(store, 100, "/treehouse/mode", "dim");
  sendFloat(store, 100, "/treehouse/brightness", 0.4f);
  TEST_ASSERT_EQUAL_FLOAT(0.4f, store.peek().masterBrightness());

  sendString(store, 100, "/treehouse/mode", "inactive");
  TEST_ASSERT_EQUAL_FLOAT(0.0f, store.peek().masterBrightness());

  sendString(store, 100, "/treehouse/mode", "active");
  TEST_ASSERT_EQUAL_FLOAT(1.0f, store.peek().masterBrightness());
}

// An operator typo must not black out the TreeHouse.
void test_unknown_mode_string_is_ignored() {
  cg::GardenStateStore store;
  sendString(store, 100, "/treehouse/mode", "dim");
  sendString(store, 200, "/treehouse/mode", "dimm");
  TEST_ASSERT_TRUE(store.peek().show_mode == cg::ShowMode::Dim);
}

void test_stale_until_first_message_then_after_the_horizon() {
  cg::GardenStateStore store(10000);
  TEST_ASSERT_TRUE(store.isStale(0));
  TEST_ASSERT_FALSE(store.hasEverReceived());

  sendFloat(store, 5000, "/flowerbeds/activity", 0.5f);
  TEST_ASSERT_TRUE(store.hasEverReceived());
  TEST_ASSERT_FALSE(store.isStale(5000));
  TEST_ASSERT_FALSE(store.isStale(15000));
  TEST_ASSERT_TRUE(store.isStale(15001));

  sendFloat(store, 16000, "/pipes/activity", 0.1f);
  TEST_ASSERT_FALSE(store.isStale(16000));
}

// An address nobody handles is not contact — it must not reset the staleness
// clock, or a stray broadcast would mask a dead Pi.
void test_unhandled_address_does_not_count_as_contact() {
  cg::GardenStateStore store(10000);
  sendFloat(store, 1000, "/lookingglass/intensity", 0.9f);
  TEST_ASSERT_TRUE(store.isStale(1000));
  TEST_ASSERT_FALSE(store.hasEverReceived());
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_folds_fabric_addresses_into_state);
  RUN_TEST(test_clamps_out_of_range_values);
  RUN_TEST(test_blowup_is_one_shot);
  RUN_TEST(test_mode_strings_and_master_brightness);
  RUN_TEST(test_unknown_mode_string_is_ignored);
  RUN_TEST(test_stale_until_first_message_then_after_the_horizon);
  RUN_TEST(test_unhandled_address_does_not_count_as_contact);
  return UNITY_END();
}

#include <unity.h>

#include <cstring>
#include <string>

#include "OscRx.h"

namespace {

// Appends an OSC string: NUL-terminated, padded out to a 4-byte boundary.
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

void pushInt(std::string& packet, int32_t value) {
  pushFloat(packet, 0.0f);  // reserve four bytes, then overwrite
  const uint32_t raw = static_cast<uint32_t>(value);
  packet[packet.size() - 4] = static_cast<char>((raw >> 24) & 0xFF);
  packet[packet.size() - 3] = static_cast<char>((raw >> 16) & 0xFF);
  packet[packet.size() - 2] = static_cast<char>((raw >> 8) & 0xFF);
  packet[packet.size() - 1] = static_cast<char>(raw & 0xFF);
}

void pushSize(std::string& packet, uint32_t size) {
  packet += static_cast<char>((size >> 24) & 0xFF);
  packet += static_cast<char>((size >> 16) & 0xFF);
  packet += static_cast<char>((size >> 8) & 0xFF);
  packet += static_cast<char>(size & 0xFF);
}

std::string floatMessage(const char* address, float value) {
  std::string packet;
  pushString(packet, address);
  pushString(packet, ",f");
  pushFloat(packet, value);
  return packet;
}

const uint8_t* bytes(const std::string& packet) {
  return reinterpret_cast<const uint8_t*>(packet.data());
}

}  // namespace

void setUp() {}
void tearDown() {}

void test_parses_float_message() {
  const std::string packet = floatMessage("/captcha/intensity", 0.625f);
  osc::Message message;

  TEST_ASSERT_TRUE(osc::parseMessage(bytes(packet), packet.size(), message));
  TEST_ASSERT_TRUE(message.is("/captcha/intensity"));
  TEST_ASSERT_FALSE(message.is("/captcha/blowup"));
  TEST_ASSERT_EQUAL_INT(1, message.argCount());
  TEST_ASSERT_EQUAL_FLOAT(0.625f, message.argFloat(0));
}

void test_parses_string_message() {
  std::string packet;
  pushString(packet, "/treehouse/mode");
  pushString(packet, ",s");
  pushString(packet, "inactive");

  osc::Message message;
  TEST_ASSERT_TRUE(osc::parseMessage(bytes(packet), packet.size(), message));
  TEST_ASSERT_EQUAL_STRING("inactive", message.argString(0));
}

void test_converts_int_argument_to_float() {
  std::string packet;
  pushString(packet, "/some/count");
  pushString(packet, ",i");
  pushInt(packet, 3);

  osc::Message message;
  TEST_ASSERT_TRUE(osc::parseMessage(bytes(packet), packet.size(), message));
  TEST_ASSERT_EQUAL_FLOAT(3.0f, message.argFloat(0));
}

// /captcha/blowup carries no arguments, and some senders omit the typetag
// entirely.  Both spellings have to parse.
void test_parses_argumentless_message_with_and_without_typetag() {
  std::string bare;
  pushString(bare, "/captcha/blowup");
  osc::Message message;
  TEST_ASSERT_TRUE(osc::parseMessage(bytes(bare), bare.size(), message));
  TEST_ASSERT_TRUE(message.is("/captcha/blowup"));
  TEST_ASSERT_EQUAL_INT(0, message.argCount());

  std::string tagged;
  pushString(tagged, "/captcha/blowup");
  pushString(tagged, ",");
  TEST_ASSERT_TRUE(osc::parseMessage(bytes(tagged), tagged.size(), message));
  TEST_ASSERT_TRUE(message.is("/captcha/blowup"));
  TEST_ASSERT_EQUAL_INT(0, message.argCount());
}

void test_missing_argument_falls_back() {
  std::string packet;
  pushString(packet, "/treehouse/brightness");
  pushString(packet, ",");

  osc::Message message;
  TEST_ASSERT_TRUE(osc::parseMessage(bytes(packet), packet.size(), message));
  TEST_ASSERT_EQUAL_FLOAT(0.25f, message.argFloat(0, 0.25f));
  TEST_ASSERT_EQUAL_STRING("none", message.argString(0, "none"));
}

void test_rejects_malformed_packets() {
  osc::Message message;
  const std::string not_an_address = "hello!!!";
  TEST_ASSERT_FALSE(osc::parseMessage(bytes(not_an_address), not_an_address.size(), message));

  TEST_ASSERT_FALSE(osc::parseMessage(nullptr, 0, message));

  // A float argument the packet is too short to actually contain.
  std::string truncated;
  pushString(truncated, "/captcha/intensity");
  pushString(truncated, ",f");
  truncated += '\0';
  TEST_ASSERT_FALSE(osc::parseMessage(bytes(truncated), truncated.size(), message));
}

void test_dispatch_unwraps_bundles() {
  const std::string first = floatMessage("/flowerbeds/activity", 0.5f);
  const std::string second = floatMessage("/pipes/activity", 0.25f);

  std::string bundle;
  pushString(bundle, "#bundle");
  for (int i = 0; i < 8; ++i) bundle += '\0';  // immediate timetag
  pushSize(bundle, static_cast<uint32_t>(first.size()));
  bundle += first;
  pushSize(bundle, static_cast<uint32_t>(second.size()));
  bundle += second;

  struct Seen {
    int count = 0;
    float flowerbeds = -1.0f;
    float pipes = -1.0f;
  } seen;

  osc::dispatch(bytes(bundle), bundle.size(),
                [](const osc::Message& message, void* context) {
                  auto* s = static_cast<Seen*>(context);
                  ++s->count;
                  if (message.is("/flowerbeds/activity")) s->flowerbeds = message.argFloat(0);
                  if (message.is("/pipes/activity")) s->pipes = message.argFloat(0);
                },
                &seen);

  TEST_ASSERT_EQUAL_INT(2, seen.count);
  TEST_ASSERT_EQUAL_FLOAT(0.5f, seen.flowerbeds);
  TEST_ASSERT_EQUAL_FLOAT(0.25f, seen.pipes);
}

void test_dispatch_ignores_a_bundle_with_a_lying_size() {
  std::string bundle;
  pushString(bundle, "#bundle");
  for (int i = 0; i < 8; ++i) bundle += '\0';
  pushSize(bundle, 9999);  // claims far more than the packet holds
  bundle += floatMessage("/pipes/activity", 1.0f);

  int calls = 0;
  osc::dispatch(bytes(bundle), bundle.size(),
                [](const osc::Message&, void* context) { ++*static_cast<int*>(context); },
                &calls);
  TEST_ASSERT_EQUAL_INT(0, calls);
}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_parses_float_message);
  RUN_TEST(test_parses_string_message);
  RUN_TEST(test_converts_int_argument_to_float);
  RUN_TEST(test_parses_argumentless_message_with_and_without_typetag);
  RUN_TEST(test_missing_argument_falls_back);
  RUN_TEST(test_rejects_malformed_packets);
  RUN_TEST(test_dispatch_unwraps_bundles);
  RUN_TEST(test_dispatch_ignores_a_bundle_with_a_lying_size);
  return UNITY_END();
}

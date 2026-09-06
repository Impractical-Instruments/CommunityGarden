#include "OscRx.h"

#include <cstring>

namespace osc {
namespace {

// OSC pads every string and blob out to a four-byte boundary.
size_t padded(size_t len) { return (len + 4) & ~static_cast<size_t>(3); }

// Length of the padded string starting at `data`, or 0 if it is unterminated
// within `len`.
size_t stringSpan(const uint8_t* data, size_t len) {
  for (size_t i = 0; i < len; ++i) {
    if (data[i] == '\0') return padded(i);
  }
  return 0;
}

uint32_t readBE32(const uint8_t* p) {
  return (static_cast<uint32_t>(p[0]) << 24) | (static_cast<uint32_t>(p[1]) << 16) |
         (static_cast<uint32_t>(p[2]) << 8) | static_cast<uint32_t>(p[3]);
}

// Bytes an argument of `type` occupies, given `remaining` bytes of payload.
// Returns -1 for a type this parser cannot skip safely.
long argSpan(char type, const uint8_t* data, size_t remaining) {
  switch (type) {
    case 'i':
    case 'f':
    case 'c':
    case 'r':
      return remaining >= 4 ? 4 : -1;
    case 'h':
    case 'd':
    case 't':
      return remaining >= 8 ? 8 : -1;
    case 'T':
    case 'F':
    case 'N':
    case 'I':
      return 0;
    case 's':
    case 'S': {
      size_t span = stringSpan(data, remaining);
      return span ? static_cast<long>(span) : -1;
    }
    case 'b': {
      if (remaining < 4) return -1;
      size_t size = readBE32(data);
      size_t span = 4 + padded(size);
      return remaining >= span ? static_cast<long>(span) : -1;
    }
    default:
      return -1;
  }
}

}  // namespace

bool Message::is(const char* pattern) const {
  return std::strcmp(address_, pattern) == 0;
}

char Message::typeAt(int index) const {
  if (index < 0 || index >= arg_count_) return '\0';
  return typetag_[index + 1];  // skip the leading ','
}

float Message::argFloat(int index, float fallback) const {
  if (index < 0 || index >= arg_count_ || args_[index] == nullptr) return fallback;
  const char type = typeAt(index);
  if (type == 'T') return 1.0f;
  if (type == 'F') return 0.0f;
  const uint32_t raw = readBE32(args_[index]);
  if (type == 'f') {
    float value;
    std::memcpy(&value, &raw, sizeof(value));
    return value;
  }
  if (type == 'i') return static_cast<float>(static_cast<int32_t>(raw));
  return fallback;
}

const char* Message::argString(int index, const char* fallback) const {
  if (index < 0 || index >= arg_count_ || args_[index] == nullptr) return fallback;
  const char type = typeAt(index);
  if (type != 's' && type != 'S') return fallback;
  return reinterpret_cast<const char*>(args_[index]);
}

bool parseMessage(const uint8_t* data, size_t len, Message& out) {
  out = Message();
  if (data == nullptr || len < 4 || data[0] != '/') return false;

  const size_t address_span = stringSpan(data, len);
  if (address_span == 0) return false;
  out.address_ = reinterpret_cast<const char*>(data);

  size_t offset = address_span;
  if (offset >= len) {
    // An address with no typetag at all.  Tolerated: /captcha/blowup is
    // sometimes sent that way by hand-rolled senders.
    out.typetag_ = ",";
    return true;
  }

  if (data[offset] != ',') return false;
  const size_t typetag_span = stringSpan(data + offset, len - offset);
  if (typetag_span == 0) return false;
  out.typetag_ = reinterpret_cast<const char*>(data + offset);

  const char* types = out.typetag_ + 1;
  offset += typetag_span;

  for (int i = 0; types[i] != '\0'; ++i) {
    if (i >= kMaxArgs) break;
    const long span = argSpan(types[i], data + offset, len - offset);
    if (span < 0) return false;  // truncated or unknown type — trust nothing after it
    out.args_[i] = data + offset;
    out.arg_count_ = i + 1;
    offset += static_cast<size_t>(span);
  }
  return true;
}

void dispatch(const uint8_t* data, size_t len, Handler handler, void* context) {
  if (data == nullptr || handler == nullptr || len < 4) return;

  if (data[0] == '#') {
    if (len < 16 || std::strncmp(reinterpret_cast<const char*>(data), "#bundle", 7) != 0) return;
    size_t offset = 16;  // "#bundle\0" + 8-byte timetag
    while (offset + 4 <= len) {
      const size_t size = readBE32(data + offset);
      offset += 4;
      if (size == 0 || offset + size > len) return;
      dispatch(data + offset, size, handler, context);  // bundles may nest
      offset += size;
    }
    return;
  }

  Message message;
  if (parseMessage(data, len, message)) handler(message, context);
}

}  // namespace osc

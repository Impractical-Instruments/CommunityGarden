// Minimal OSC 1.0 receive-side parser.
//
// Vendored rather than pulled from a library because the TreeHouse controllers
// only ever receive six addresses carrying a float, a string, or nothing at all
// (ADR-0020).  A parser this small can be unit-tested on the host, which a
// hardware-bound library cannot.
//
// Nothing here allocates: a Message borrows pointers into the caller's packet
// buffer and is only valid while that buffer lives.

#pragma once

#include <cstddef>
#include <cstdint>

namespace osc {

constexpr int kMaxArgs = 8;

class Message {
 public:
  const char* address() const { return address_; }

  // True when address() equals `pattern` exactly.  No wildcard matching —
  // the Fabric does not use it.
  bool is(const char* pattern) const;

  int argCount() const { return arg_count_; }
  char typeAt(int index) const;

  // Reads argument `index` as a float.  Ints are converted; anything else
  // (or an out-of-range index) yields `fallback`.
  float argFloat(int index, float fallback = 0.0f) const;

  // Reads argument `index` as a string, or `fallback` if it is not one.
  const char* argString(int index, const char* fallback = "") const;

 private:
  friend bool parseMessage(const uint8_t*, size_t, Message&);

  const char* address_ = "";
  const char* typetag_ = "";
  int arg_count_ = 0;
  const uint8_t* args_[kMaxArgs] = {nullptr};
};

// Parses one OSC message.  Returns false on a malformed or truncated packet.
bool parseMessage(const uint8_t* data, size_t len, Message& out);

using Handler = void (*)(const Message& message, void* context);

// Parses a packet and invokes `handler` for every message in it.  Handles both
// a bare message and a `#bundle`, including nested bundles.  Malformed
// elements are skipped rather than aborting the whole packet.
void dispatch(const uint8_t* data, size_t len, Handler handler, void* context);

}  // namespace osc

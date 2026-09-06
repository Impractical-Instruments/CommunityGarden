#include "Net.h"

#include <WiFi.h>
#include <WiFiUdp.h>

#include "net_config.h"
#include "secrets.h"

namespace cg {
namespace {

WiFiUDP g_udp;
uint8_t g_packet[512];  // largest thing the Fabric sends is a short bundle

constexpr uint32_t kMaxBackoffMs = 30000;

IPAddress fromOctets(const uint8_t octets[4]) {
  return IPAddress(octets[0], octets[1], octets[2], octets[3]);
}

}  // namespace

void Net::begin(const char* hostname, const uint8_t ip[4], uint16_t osc_port) {
  hostname_ = hostname;
  port_ = osc_port;

  static uint8_t kGateway[4] = CG_LAN_GATEWAY;
  static uint8_t kNetmask[4] = CG_LAN_NETMASK;

  WiFi.mode(WIFI_STA);
  WiFi.setHostname(hostname_);
  WiFi.setSleep(false);  // sleep adds tens of ms of jitter to Garden State
  WiFi.setAutoReconnect(true);

  if (!WiFi.config(fromOctets(ip), fromOctets(kGateway), fromOctets(kNetmask),
                   fromOctets(kGateway))) {
    Serial.println("[net] static IP config rejected - falling back to DHCP");
  }

  connect(millis());
}

void Net::connect(uint32_t now_ms) {
  Serial.printf("[net] connecting to \"%s\"\n", WIFI_SSID);
  WiFi.disconnect();
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  next_attempt_ms_ = now_ms + backoff_ms_;
}

void Net::poll(uint32_t now_ms) {
  const bool connected = isConnected();

  if (connected && !was_connected_) {
    backoff_ms_ = 1000;
    if (!udp_started_) {
      g_udp.begin(port_);
      udp_started_ = true;
    }
    Serial.printf("[net] up as %s on %s:%u\n", hostname_, localIp().toString().c_str(), port_);
  } else if (!connected && was_connected_) {
    Serial.println("[net] link lost - animating from last known Garden State");
  }
  was_connected_ = connected;

  if (!connected && static_cast<int32_t>(now_ms - next_attempt_ms_) >= 0) {
    backoff_ms_ = min(backoff_ms_ * 2, kMaxBackoffMs);
    connect(now_ms);
  }
}

int Net::receive(osc::Handler handler, void* context) {
  if (!udp_started_) return 0;

  int packets = 0;
  for (int size = g_udp.parsePacket(); size > 0; size = g_udp.parsePacket()) {
    const int read = g_udp.read(g_packet, sizeof(g_packet));
    if (read > 0) {
      osc::dispatch(g_packet, static_cast<size_t>(read), handler, context);
      ++packets;
    }
    if (packets > 32) break;  // never let a packet storm starve the frame loop
  }
  return packets;
}

bool Net::isConnected() const { return WiFi.status() == WL_CONNECTED; }

IPAddress Net::localIp() const { return WiFi.localIP(); }

}  // namespace cg

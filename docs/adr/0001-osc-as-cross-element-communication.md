# OSC as the cross-element communication fabric

**Status:** Accepted and amended by [ADR-0007](0007-osc-fabric-schema.md)

*Note, 2026-11-18: addresses and ports are in `ShowControl/network.json` (ADR-0007), not in each Element's `settings.json` as the last paragraph says.*

All inter-element communication in The Community Garden uses OSC (Open Sound Control) over UDP on a local Ethernet network. OSC is the lingua franca of live performance technology — it is already used within each Element (Python → Arduino → Dynamixel, Max → audio hardware), so extending it between Elements keeps the whole system on one protocol. It is fire-and-forget (appropriate for show control, where a dropped message is preferable to a blocked thread), has near-zero latency on a local LAN, and requires no broker or server infrastructure. The alternative — REST or WebSocket over HTTP — would require a running server process and adds failure modes that are hard to debug in a live performance setting.

## Consequences

Any Element can send to any other by targeting its IP and port. There is no discovery mechanism; addresses and ports are configured statically in each Element's `settings.json`. This is a deliberate constraint: static config is simpler to reason about and debug during a festival than dynamic service discovery.

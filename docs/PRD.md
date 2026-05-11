# Product Requirements Document — The Community Garden

**Version:** 1.0
**Author:** Charlie Huguenard
**Festival debut:** Connect Beyond Festival, May 29–31 2026
**Status:** Living document — update as decisions are confirmed

---

## 1. What Is This

The Community Garden is a touring interactive installation. Four Elements — FlowerBeds, TreeHouse, Playing the Pipes, and FundingCAPTCHA — inhabit a shared physical space and respond to visitors. The Elements can operate independently but are designed to communicate with each other, with the TreeHouse acting as the Hub that reflects the aggregate state of the garden.

The installation travels after Connect Beyond Festival. It is designed to be installed and deinstalled quickly, with no fragile per-machine configuration.

### Thematic intent

Each Element engages a different facet of how systems — natural, technological, bureaucratic, and social — mediate human experience:

| Element | Theme |
|---|---|
| FlowerBeds | Surveillance and self-image: the flowers follow you and show you yourself being followed |
| Playing the Pipes | The flow of utilities through infrastructure; the flow of money and influence through society |
| TreeHouse | The world these tensions inhabit; a natural home suspended by and entangled with technology |
| FundingCAPTCHA | Proving your humanity to a machine; the fear of relinquishing control to systems with no recourse |

The tone varies: FlowerBeds is a lighthearted poke; FundingCAPTCHA is pointed satire.

---

## 2. Visitor Experience

### Spatial layout

```
[Entrance]
    │
    ▼
[FlowerBeds]  ← flowers track visitors as they enter
    │
    ▼
[TreeHouse]   ← centrepiece, 9.5 ft tall (3 ft base + house)
   / \
  /   \
[Playing   [FundingCAPTCHA]
 the Pipes]
```

### Journey

1. **Arrival** — Visitors enter and FlowerBeds flowers (mirror-centred, servo-driven) begin tracking them. The flowers watch the visitors; the mirrors show the visitors watching themselves being watched.
2. **Discovery** — Visitors see the TreeHouse: hyper-realistic exterior, otherworldly inside glimpsed through plexiglass windows. Branches on the roof grow and wither. An operable front door lets visitors reach in and interact with a diorama.
3. **Playing the Pipes** — Pipes and conduit grow out of the base of the TreeHouse. Visitors discover valves and switches and begin steering the music system. Controls affect the character of the sound — Tiller Control, not direct instrument play.
4. **FundingCAPTCHA** — On the other side of the TreeHouse: a 7-foot kiosk styled as a CRT monitor. Visitors play increasingly frustrating CAPTCHA-inspired games on a projected touch screen to "prove their humanity."

Throughout, the TreeHouse responds to activity across all Elements, updating its displays to reflect the Garden State.

---

## 3. Elements

### 3.1 FlowerBeds

**Status:** Battle-tested at weekend event; scaling to production configuration now.

**What it does:** Depth camera detects visitors as Blobs. Blobs are stabilised into Blob Tracks. Tracks are assigned to nearby FlowerClusters. Each cluster rotates its servo-driven flower toward the nearest visitor. Flowers have mirrors at their centres.

**Production configuration:**
- 1 depth camera (Orbbec), overhead mount — single-camera coverage confirmed (tested 2026-04-30)
- 2 controller boards (OpenRB-150), 24 Dynamixel XL430-W250-T servos each = 48 flowers total, 12 modules × 4 clusters
- OSC over UDP to controllers at `192.168.1.50` and `192.168.1.51`

**OSC output to fabric:**
- TBD — at minimum, visitor count / activity level for TreeHouse to consume

---

### 3.2 TreeHouse

**Status:** Physical structure under construction; LED effects and video kaleidoscope work beginning now.

**What it does:** A 9.5-foot physical structure (3-foot base, ~6.5-foot house) with:
- **Exterior:** Hyper-realistic construction, appears to have been ripped from the ground; clouds on strings hold it up
- **Interior:** Otherworldly; visible through plexiglass windows
- **Branches:** Grow and wither on the roof in response to Garden State
- **Front door:** Operable; visitors can reach in to interact with a diorama
- **Dioramas:** Multiple interior scenes lit and animated (House Swarming, Club chase, Forge & Flora arc-to-bloom crossfade, Looking Glass generative video kaleidoscope)

**LED hardware:** Two Pi Picos (MicroPython + PIO) drive 8 SK6812 RGBW channels from the garage tech bay. Pico A: dioramas + Forge & Flora (5 channels). Pico B: Dormer, Porch Lights, Attic TV & Lamps (3 channels). All channels use stable udev device names. See ADR-0010.

**Hub role:** Receives activity signals from FlowerBeds, Playing the Pipes, and FundingCAPTCHA over the OSC Fabric. Expresses aggregate Garden State through its displays and animations. Exact mapping of input signals to display outputs is a design decision in progress.

**Open question:** Exact branch growth → Garden State mapping is TBD.

---

### 3.3 Playing the Pipes

**Status:** Physical construction underway by a teammate.

**What it does:** A Dr. Seuss/Rube Goldberg tangle of water pipes and electrical conduit fitted with valves and switches. Visitors operate the controls to steer a music system running granulators and loop players on a Raspberry Pi (Cycling '74 Max/RNBO). Controls use Tiller Control — visitors change the direction and character of the music, not trigger discrete notes.

**Hardware path (confirmed 2026-05-07):** Direct sensor → Pi/Max. Physical controls (rotary encoders, switches) are read by a Python GPIO bridge process on the Pi; the bridge sends OSC to the RNBO runner, which handles all audio DSP and emits `/pipes/activity` to the TreeHouse directly. No microcontroller intermediary. Note: RNBO runner cannot read GPIO directly — the bridge process is required.

**OSC output to fabric:** Playing the Pipes is an emitter only — it sends activity signals outward (controls active, engagement level) and does not receive from other Elements. It is a pure sound piece; external OSC input would conflict with the Tiller Control experience.

---

### 3.4 FundingCAPTCHA

**Status:** Pygame implementation complete; browser stack deleted. Festival debut May 29.

**What it does:** A 7-foot kiosk styled as a CRT monitor running a suite of increasingly frustrating CAPTCHA-inspired touch-screen games. Visitors must "prove their humanity" to progress.

**Touch screen approach:** Front-projection onto the kiosk face using a BenQ LH830ST short-throw laser projector, with Orbbec depth camera co-mounted on the projector for shared orientation and simpler coordinate mapping. Camera detects finger contacts close to the projection surface. Coordinate calibration required per installation (camera-to-screen mapping). See ADR-0004 and ADR-0011.

**Software architecture:** A single unified pygame process (`app.py`) owns the display, camera pipeline, touch calibration, game rotation, and a lightweight monitoring WebSocket. No browser. See ADR-0012.

**Games (pygame):** UpsideDown, Rhythm, Keepaway. All must self-terminate on inactivity (see ADR-0003).

**Photos:** Kid-designed images live in `images/`. Per-game config files (`pairs.json`, `rhythm-images.json`, `keepaway-images.json`) map filenames; all default to `[]` with emoji fallback. No upload endpoint — operator copies images locally before show.

**OSC output to fabric:**
- TBD — activity signals (game started, game completed, game failed, frustration level) for TreeHouse to consume

---

## 4. Cross-Element Communication

### OSC Fabric

All Elements communicate over OSC/UDP on the Show Network. Any Element may send to or receive from any other. Current known data flows:

| Source | Destination | What |
|---|---|---|
| FlowerBeds | TreeHouse | Visitor presence / activity level |
| Playing the Pipes | TreeHouse | Control activity / engagement level |
| FundingCAPTCHA | TreeHouse | Game activity / events |

OSC address schema and message formats are TBD per Element. Each Element's show-control software is responsible for publishing its own OSC output. The TreeHouse is responsible for subscribing to and interpreting incoming signals.

### Garden State

Garden State is the TreeHouse's internal representation of activity across the installation. It drives reactive displays (branch growth/wither, diorama state changes, etc.). The exact mapping from incoming OSC signals to Garden State expressions is a design decision in progress — intentionally left open.

---

## 5. Shared Infrastructure

### IIVision

Shared computer-vision library providing depth camera abstraction, blob detection, blob stabilisation, and coordinate transforms. Used by FlowerBeds and FundingCAPTCHA.

**Festival scope:** IIVision must reliably serve FlowerBeds (3D people detection) and FundingCAPTCHA (2D surface touch detection). Generalising it for broader use is a post-festival aspiration, not a requirement.

### Show Network

Isolated Ethernet LAN connecting all show computers. All OSC communication travels over this network. Devices should be assigned static IPs (hardcoded in `settings.json` per element, not per machine).

---

## 6. Operational Requirements

### Uptime

- Runs continuously ~10 hours/day for 3 days (May 29–31)
- Handles hundreds of visitors per day
- Each Element must recover automatically from crashes (process supervisor / watchdog)
- Failure of one Element must not affect other Elements

### Monitoring Dashboard

A phone-accessible web interface (accessible on the Show Network, optionally via internet if simple to add) with:

1. **Status page** — up/down status per Element; last crash reason if available
2. **Log page** — unified sequential log stream from all Elements
3. **Per-element pages** — custom UI per Element (FlowerBeds has its existing top-down visualizer; others TBD)

### Remote Access

- SSH access to all show computers on the Show Network (password auth on isolated LAN)
- No internet uplink — monitoring is LAN-only for the festival

### Installation & Deinstallation

- Designed to tour — quick install and deinstall
- No per-machine configuration: all config lives in `settings.json` files, not in code or environment
- Network addresses, motor IDs, camera serials: all in config, never hardcoded

---

## 7. Out of Scope (for festival)

- IIVision generalisation for third-party use
- Inter-element communication beyond TreeHouse-as-hub (e.g., FundingCAPTCHA → Playing the Pipes)
- Automated testing / CI pipeline
- Any persistent data collection from visitors

---

## 8. Open Questions

| # | Question | Status |
|---|---|---|
| 1 | Can one Orbbec camera cover the full 48-cluster FlowerBeds field? | **Resolved 2026-04-30: yes, single camera confirmed** |
| 2 | FundingCAPTCHA: does front-projection + co-mounted camera give reliable touch detection? | **Untested — Week 1 priority, see issue #73** |
| 3 | Playing the Pipes: direct sensor → Pi/Max, or microcontroller → OSC? | **Resolved 2026-05-07: direct GPIO → Python bridge → RNBO runner → OSC. See issue #49.** |
| 4 | OSC message schema for each Element's output to the fabric | Largely resolved via ADR-0007; see `ShowControl/network.json` |
| 5 | TreeHouse: exact mapping of Garden State inputs to branch/display outputs | In progress — ADR-0008 covers displays; branch weights configurable per-motor in `settings.json` |
| 6 | Playing the Pipes: audio system for venue | **Resolved 2026-05-07: 4× studio monitors (Event series). Pi 5 has no analog audio — USB audio interface required.** |
| 6 | Monitoring dashboard: build as central aggregator service or per-element push? | TBD |
| 7 | Internet uplink for remote monitoring: worth adding for festival? | TBD |

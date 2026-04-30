# The Community Garden

A touring interactive installation that puts visitors inside a world of systems — natural, technological, bureaucratic, and social — and lets them feel those systems respond to their presence.

## Language

### The Installation

**The Community Garden**:
The name of the full interactive experience. Contains four Elements that can operate independently or together in a shared physical space.
_Avoid_: "the show", "the project", "the system"

**Element**:
One of the four self-contained interactive components of The Community Garden. Each Element has its own show-control software, hardware, and thematic intent, but can send and receive OSC messages from other Elements.
_Avoid_: "system", "module", "component", "installation" (when referring to a single element)

**Visitor**:
A person experiencing The Community Garden. Not a user, not an audience member — they interact physically with the space and the Elements within it.
_Avoid_: "user", "audience", "player" (except within FundingCAPTCHA context)

**Hub**:
The TreeHouse's role in the installation — it receives state signals from all other Elements and reflects the aggregate activity of the garden through its displays and animations.
_Avoid_: "controller", "master", "server"

**Garden State**:
The aggregate picture of visitor activity across all Elements at a given moment. The TreeHouse uses Garden State to drive its reactive displays (branch growth, diorama states, etc.).

### Elements

**FlowerBeds**:
The Element at the entrance. Servo-driven flowers with mirrors at their centres track visitors using depth-camera blob detection. Thematic intent: surveillance and self-image — the flowers follow you, and show you yourself being followed.

**TreeHouse**:
The centrepiece Element. A 9.5-foot physical structure (3-foot base + house) that looks hyper-realistic on the outside and otherworldly inside. Visitors peer in through plexiglass windows; one front door is operable and lets visitors reach in to interact with a diorama. Branches on the roof grow and wither in response to Garden State. The Hub of the installation.

**Playing the Pipes**:
The Element growing out of the base of the TreeHouse — a Dr. Seuss/Rube Goldberg tangle of water pipes and electrical conduit fitted with valves and switches. Visitors steer a music system (granulators, loop players) by operating the controls. Thematic intent: the literal flow of utilities through infrastructure, and the figurative flow of money and influence through society.
_Avoid_: "playing music", "triggering notes" — visitors *steer* the music, they do not play it directly

**FundingCAPTCHA**:
The Element on the opposite side of the TreeHouse from Playing the Pipes. A 7-foot-tall kiosk styled as a CRT monitor, running a browser-based suite of increasingly frustrating CAPTCHA-inspired games on a touch screen. Thematic intent: the frustration and irony of humans proving their humanity to robots; the fear of relinquishing control to systems that may malfunction with no recourse.

### Control Model

**Tiller Control**:
The control metaphor for Playing the Pipes. Visitors steer the music like a boat — controls affect the direction and character of the music rather than triggering discrete notes or sounds. Contrast with direct instrument control.
_Avoid_: "playing", "triggering", "note input"

**Blob**:
A detected human presence in 3D world space, produced by depth-camera background subtraction and connected-component analysis. The fundamental unit of visitor detection in IIVision.

**Blob Track**:
A stabilised, identity-consistent blob across multiple frames. A raw Blob becomes a Blob Track after surviving confirmation and receiving EMA-smoothed position updates.

### Infrastructure

**IIVision**:
The shared computer-vision library (depth camera abstraction, blob detection, blob stabilisation, coordinate transforms). Used by FlowerBeds and FundingCAPTCHA; intended to be general enough for any vision-based interactive installation.

**OSC Fabric**:
The UDP/OSC network that connects Elements when co-located. Any Element may send or receive OSC messages from any other Element. The TreeHouse is the primary consumer of cross-element messages, but the fabric is intentionally open.

**Show Network**:
The isolated Ethernet LAN that connects all show computers during installation. All OSC communication travels over the Show Network. May be extended with an internet uplink for remote monitoring.

## Relationships

- **The Community Garden** contains four **Elements**
- Each **Element** operates independently or participates in the **OSC Fabric**
- **TreeHouse** is the **Hub** — it aggregates signals from all other Elements to express **Garden State**
- **Playing the Pipes** physically extends from the base of **TreeHouse**
- **FundingCAPTCHA** is positioned on the opposite side of **TreeHouse** from **Playing the Pipes**
- **FlowerBeds** is at the entrance, the first Element a **Visitor** encounters
- **IIVision** is used by **FlowerBeds** and **FundingCAPTCHA** for **Visitor** detection

## Example dialogue

> **Dev:** "When a Visitor spends a long time at FundingCAPTCHA, does the TreeHouse react?"
> **Domain expert:** "Yes — FundingCAPTCHA sends activity signals over the OSC Fabric, which the TreeHouse uses to update Garden State. That might mean branches growing, or a diorama changing state. The exact mapping is TBD."

> **Dev:** "Is Playing the Pipes a MIDI instrument?"
> **Domain expert:** "No — it uses Tiller Control. Visitors steer the music, they don't play notes. The valves and switches affect parameters in the granulators and loop players."

## Flagged ambiguities

- "module" has two meanings in this repo: a `FlowerModule` in FlowerBeds code (a physical grouping of flower clusters), and colloquially "one of the four parts of the show." Use **Element** for the latter.

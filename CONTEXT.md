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
The Element on the opposite side of the TreeHouse from Playing the Pipes. A 7-foot-tall kiosk styled as a CRT monitor. A short-throw laser projector (mounted overhead, ~3 feet from the Screen) projects the game interface onto a vertical projection surface; an Orbbec depth camera co-mounted with the projector detects hands touching or approaching the Screen. Thematic intent: the frustration and irony of humans proving their humanity to robots; the fear of relinquishing control to systems that may malfunction with no recourse.

**Screen** (FundingCAPTCHA):
The vertical projection surface on the front of the FundingCAPTCHA kiosk. Visitors interact by physically touching the Screen; the depth camera detects contact (and near-contact within a configurable depth threshold) and converts it to tap-down and tap-up events on a grid. One to three Players can touch the Screen simultaneously.
_Avoid_: "touch screen" (implies a capacitive panel), "canvas", "display"

**Player** (FundingCAPTCHA):
A Visitor who is actively touching or about to touch the Screen. FundingCAPTCHA is the only Element where "Player" is appropriate; elsewhere use Visitor. Play is drop-in/drop-out — there is no formal join or leave event.

**Arc**:
The lifecycle of a single game in FundingCAPTCHA. Difficulty ramps from easy to unmanageable as Players succeed; the Arc always ends in a spectacular inevitable failure (the Blow-Up) rather than a clean win. Winning a round only advances the difficulty — there is no overall victory condition. Every game type must guarantee a loss after sustained inactivity — either through a literal countdown timer, or through mechanics that ensure failure without Player input (e.g. defenders eventually catching the ball carrier in Keepaway).
_Avoid_: "session", "run", "level" (a level is one stage within an Arc, not the Arc itself)

**Blow-Up**:
The spectacular end-of-Arc failure state when difficulty has ramped beyond what Players can manage. Intentionally rewarding — lots of visual and audio fanfare — so that failing after a long Arc feels like a payoff, not a punishment. After a Blow-Up the kiosk cycles to the next game.

**Show Mode**:
The operational mode for live installation. Game selection is automated: the kiosk cycles through game types as each Arc ends using a shuffle-bag algorithm (all game types are played in random order before any repeats). The game selection screen is hidden.
_Avoid_: "production mode", "performance mode"

**Screensaver**:
The idle state displayed when no Players have touched the Screen for a configurable period after a game has ended. Because every Arc is guaranteed to end in a loss on its own, the Screensaver only needs to monitor the between-game state — it never interrupts an active Arc. Touching the Screen exits the Screensaver and starts a game. Multiple screensavers available, inspired by classic procedural screensavers (e.g. the Windows pipes screensaver).
_Avoid_: "attract screen", "idle animation", "lobby"

### FundingCAPTCHA Domain

**Round**:
One complete level within an Arc. A Round ends in either a win (difficulty increases, next Round begins) or a loss (Blow-Up, Arc ends). Each game type defines its own win and loss conditions per Round.

**Intensity**:
A continuous 0.0–1.0 value sent over the OSC Fabric to the TreeHouse each frame, representing how far the current Arc has progressed toward its Blow-Up. Derived from the current difficulty level normalised against the maximum. Resets to 0.0 at the start of each new Arc.
_Avoid_: "difficulty", "score", "engagement level"

**Blow-Up Signal**:
A one-shot OSC message sent to the TreeHouse when a Blow-Up occurs, triggering a reactive moment in the TreeHouse displays and animations. Distinct from Intensity — it is an event, not a continuous value.

### FlowerBeds Domain

**Attraction**:
The policy that governs which Visitor a FlowerCluster looks at. Combines three weighted scores — proximity, dwell time, and inertia — to pick the best target each frame. Both the tuning parameters and the scoring computation live here.
_Avoid_: AttractionConfig, attraction config, scoring weights

**FlowerCluster**:
A single servo motor at a fixed world position. Each frame it consults its Attraction policy to select a target Visitor and returns a motor command pointing toward them.

**Dwell**:
The number of consecutive frames a Visitor has been within a FlowerCluster's influence radius. Higher dwell increases that Visitor's attraction score, causing flowers to prefer lingering visitors over passing ones.

**Inertia**:
The bonus score applied to the Visitor a FlowerCluster targeted last frame. Prevents jittery switching between nearby visitors of similar distance.

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

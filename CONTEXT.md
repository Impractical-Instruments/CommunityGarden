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
The complete set of live signals from all Elements and show-control inputs, collected by the TreeHouse Coordinator from incoming OSC messages and passed to every Controllable each frame. Contains raw per-Element values — not a pre-computed aggregate. Each Controllable reads whichever fields it cares about and applies its own weighting/response logic internally.

Fields:
- `flowerbeds_activity` (float 0–1) — normalised visitor activity from FlowerBeds
- `captcha_intensity` (float 0–1) — Arc progress toward Blow-Up from FundingCAPTCHA
- `captcha_blowup` (bool) — one-shot flag, true on the frame a Blow-Up fires
- `pipes_activity` (float 0–1) — normalised music engagement from Playing the Pipes
- `show_mode` (enum: full/dim/off) — global show control state
- `brightness` (float 0–1) — global brightness override

### Elements

**FlowerBeds**:
The Element at the entrance. Servo-driven flowers with mirrors at their centres track visitors using depth-camera blob detection. Thematic intent: surveillance and self-image — the flowers follow you, and show you yourself being followed.

**TreeHouse**:
The centrepiece Element. A 9.5-foot physical structure (3-foot base + house) that looks hyper-realistic on the outside and otherworldly inside. Visitors peer in through plexiglass windows; one front door is operable and lets visitors reach in to interact with a diorama. Branches on the roof grow and wither in response to Garden State. The Hub of the installation.

**Playing the Pipes**:
The Element growing out of the base of the TreeHouse — a Dr. Seuss/Rube Goldberg tangle of water pipes and electrical conduit fitted with valves and switches. Visitors steer a music system (granulators, loop players) by operating the controls. Thematic intent: the literal flow of utilities through infrastructure, and the figurative flow of money and influence through society.
_Avoid_: "playing music", "triggering notes" — visitors *steer* the music, they do not play it directly

**FundingCAPTCHA**:
The Element on the opposite side of the TreeHouse from Playing the Pipes. A 7-foot-tall kiosk styled as a CRT monitor. A short-throw laser projector projects the game interface onto the Screen; an Orbbec depth camera mounted on the kiosk facing toward Players captures their silhouettes at configured depth ranges. Players interact by making shapes with their bodies — their silhouettes activate cells on a projected grid. Thematic intent: the frustration and irony of humans proving their humanity to robots; the fear of relinquishing control to systems that may malfunction with no recourse.

**Screen** (FundingCAPTCHA):
The vertical projection surface on the front of the FundingCAPTCHA kiosk. Displays game content and live Player silhouettes so Players can see their own shapes and how they map to the grid. Players interact by standing in front of the kiosk — not by touching the Screen.
_Avoid_: "touch screen" (implies contact input), "canvas", "display"

**Player** (FundingCAPTCHA):
A Visitor standing in the Play Zone in front of the FundingCAPTCHA kiosk. FundingCAPTCHA is the only Element where "Player" is appropriate; elsewhere use Visitor. Play is drop-in/drop-out — there is no formal join or leave event.

**Arc**:
The lifecycle of a single game in FundingCAPTCHA. Difficulty ramps from easy to unmanageable as Players succeed; the Arc always ends in a spectacular inevitable failure (the Blow-Up) rather than a clean win. Winning a round only advances the difficulty — there is no overall victory condition. Every game type must guarantee a loss after sustained inactivity — either through a literal countdown timer, or through mechanics that ensure failure without Player input (e.g. defenders eventually catching the ball carrier in Keepaway).
_Avoid_: "session", "run", "level" (a level is one stage within an Arc, not the Arc itself)

**Blow-Up**:
The spectacular end-of-Arc failure state when difficulty has ramped beyond what Players can manage. Intentionally rewarding — lots of visual and audio fanfare — so that failing after a long Arc feels like a payoff, not a punishment. After a Blow-Up the kiosk cycles to the next game.

**Show Mode**:
The operational mode for live installation. Game selection is automated: the kiosk cycles through game types as each Arc ends using a shuffle-bag algorithm (all game types are played in random order before any repeats). The game selection screen is hidden.
_Avoid_: "production mode", "performance mode"

**Screensaver**:
The idle state displayed when no Players are in the Play Zone after an Arc has ended. Because every Arc is guaranteed to end in a loss on its own, the Screensaver only needs to monitor the between-Arc state — it never interrupts an active Arc. A Player entering the Play Zone and remaining for `attract_dwell_s` exits the Screensaver and starts a new Arc. Multiple screensavers available, inspired by classic procedural screensavers (e.g. the Windows pipes screensaver).
_Avoid_: "attract screen", "idle animation", "lobby"

### FundingCAPTCHA Domain

**Game** (FundingCAPTCHA):
A defined set of mechanics (code in `games/`) paired with a Level set (data in a config file). Examples: BodyGrid, UpsideDown, Rhythm, Keepaway. `app.py` loads all Games and plays them in shuffle-bag order. Each Arc plays exactly one Game from start through Blow-Up.
_Avoid_: "game type", "mode"

**Level**:
One authored puzzle definition within a Game. For BodyGrid: specifies a prompt string, a background image, a grid size, a set of `valid_cells` (col/row pairs the Player must cover), a designer-assigned difficulty (1–5), and optional per-level overrides for timer duration, hold dwell, and hint opacity. An Arc picks Levels by shuffle-bag from those at equal or one step harder difficulty than the last Level beaten — there is no fixed ordering. Timer expiry triggers a Blow-Up; beating a Level only escalates difficulty.
_Avoid_: "round", "stage", "difficulty step"

**Play Zone**:
The set of depth ranges in front of the FundingCAPTCHA camera where Player pixels contribute to the silhouette. Defined as one or more Depth Slabs. Pixels outside all slabs appear as holes in the silhouette. A "too close" implicit exclusion zone (below the `near_mm` of the nearest slab) prevents Players from blocking the camera entirely.
_Avoid_: "detection zone", "active area"

**Depth Slab**:
A single depth band `[near_mm, far_mm]` with an associated `slab_id`. Pixels within a Depth Slab render with that slab's configured color and carry its game-defined role. Two slabs may share a `slab_id` (non-contiguous bands, identical behavior). Configured as `depth_slabs` in `captcha-settings.json`.
_Avoid_: "depth layer", "depth band" (use Depth Slab)

**Intensity**:
A continuous 0.0–1.0 value sent over the OSC Fabric to the TreeHouse each frame, representing how far the current Arc has progressed toward its Blow-Up. Computed as a configurable weighted sum of current difficulty (normalised 0–1 over max difficulty 5) and time pressure (elapsed / timer_s for the current Level). Weights live in `captcha-settings.json`. Resets to 0.0 at the start of each new Arc.
_Avoid_: "difficulty", "score", "engagement level"

**Blow-Up Signal**:
A one-shot OSC message sent to the TreeHouse when a Blow-Up occurs, triggering a reactive moment in the TreeHouse displays and animations. Distinct from Intensity — it is an event, not a continuous value. The TreeHouse reacts with a **Blow-Up Reaction**: attic lights spike to full brightness then decay along an exponential curve back to the Garden-State-driven level. Decay shape (time constant, optional tail flicker) is configurable.

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

### TreeHouse Domain

**Diorama**:
A self-contained miniature room visible through a TreeHouse window. Three dioramas exist: House Swarming (ground floor), Club (second floor), and Mycelium (second floor). Each is its own LEDControllable with distinct Garden-State-reactive animation.

**House Swarming**:
Ground floor diorama. Lit with SK6812 RGBW strips using an incandescent-style pattern.

**Club**:
Second floor diorama. Lit with SK6812 strips using a chase/strobe pattern.

**Mycelium**:
Second floor diorama. Contains clay mushrooms and edge-lit acrylic panels masked so the glow traces mycelium network patterns. LED light enters through acrylic edges and illuminates the masked paths. 224 LEDs total on one SK6812 channel. Animation logic pulses or propagates along the mycelium paths in response to Garden State rather than applying uniform brightness.

**Attic**:
The interior space at the top of the TreeHouse, behind the gable windows and dormer. Functionally houses branch motors, wiring, and rigging. Visually dressed as an upside-down TV den — furniture and lamps mounted to the ceiling, a TV mounted so it faces the floor (ceiling from the visitor's perspective). Visitors see only ambient glow through the clear acrylic gable windows: the TV glow and warm lamp light. The TV is not directly visible from the front.

**Attic TV**:
A prop television mounted upside-down inside the Attic. Contains LED strips (not a real screen) that cast a cool blue-white flicker glow onto the ceiling and walls — the sickly ambience of late-night TV watching. Visible to visitors only as indirect glow through the gable windows. Driven as a standard Pico LED channel; "TV glow" is a flicker pattern in a cool blue-white color. Reactive to Garden State (brightness/intensity of flicker). Shares an SK6812 channel with the Attic Lamps (8 LEDs total).

**Controllable**:
The base abstraction for everything the TreeHouse controls. Two methods: `update(dt, state)` advances internal state by `dt` seconds given the current `GardenState`; `get_state()` returns a serialisable snapshot for monitoring. Every display, motor controller, and video output in the TreeHouse is a Controllable.
_Avoid_: "Display" (the old name — being replaced)

**LEDControllable**:
A Controllable subclass for anything that drives SK6812 RGBW LED strips via a Pico. Adds `get_pixels()` returning a list of `ChannelFrame` objects (one per Pico GPIO pin). Two `PicoDriver` instances (one per Pico) collect pixels from their assigned LEDControllables each frame and send them. Each room/space is its own LEDControllable subclass with its own Garden-State-reactive animation logic.
_Avoid_: "LEDDisplay" (the old name — being replaced), conflating with `Controllable`

**GardenState**:
A dataclass passed to every `Controllable.update()` each frame. Fields: `bloom` (0.0–1.0 Branch extension target), `intensity` (0.0–1.0 aggregate visitor activity), `blowup_triggered` (bool, one-shot per Blow-Up event). Each Controllable reads only the fields relevant to it.

**Attic Lamps**:
One or two physical lamp props (floor or table lamps) mounted upside-down in the Attic. Provide warm ambient fill light visible through the gable windows. Share an SK6812 channel with the Attic TV (8 LEDs total across both TV and lamps).

**Branch**:
One of 4–6 motorised branches mounted on the TreeHouse roof. Each Branch extends (blooms) or retracts (withers) independently via a Dynamixel servo driving a lead screw that pushes a wire with leaves/blooms through a PVC housing dressed as a tree branch. The aggregate extension state follows a 0.0–1.0 Bloom value: 0.0 = fully retracted/dead, 1.0 = fully extended/bloomed.
_Avoid_: "arm", "limb", "antenna"

**Bloom**:
A 0.0–1.0 continuous value representing the aggregate extension state of all Branches. Driven by Garden State. Individual Branches track Bloom with per-branch configurable phase offsets, max-extension speed, and noise — all tunable in `settings.json` — so branches stagger organically rather than moving in lockstep.
_Avoid_: "position", "extension level", "growth"

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
The shared computer-vision library (depth camera abstraction, background subtraction, blob detection, blob stabilisation, coordinate transforms). Used by FlowerBeds (full pipeline: blob detection + stabilisation) and FundingCAPTCHA (background subtraction + denoising only — blob detection not used). Intended to be general enough for any vision-based interactive installation.

**OSC Fabric**:
The UDP/OSC network that connects Elements when co-located. Any Element may send or receive OSC messages from any other Element. The TreeHouse is the primary consumer of cross-element messages, but the fabric is intentionally open.

Established OSC addresses (inbound to TreeHouse):

| Address | Type | Sender | Meaning |
|---|---|---|---|
| `/treehouse/mode` | string | operator | `"full"` / `"dim"` / `"off"` — show mode override |
| `/treehouse/brightness` | float 0–1 | operator | dim level override |
| `/captcha/intensity` | float 0–1 | FundingCAPTCHA | Arc progress toward Blow-Up |
| `/captcha/blowup` | (no args) | FundingCAPTCHA | one-shot Blow-Up event |
| `/flowerbeds/activity` | float 0–1 | FlowerBeds | normalised visitor activity |
| `/pipes/activity` | float 0–1 | Playing the Pipes | normalised music engagement |

**Signal Bag**:
A pattern used inside individual Controllable implementations (not at the Coordinator level) to combine a subset of Garden State fields into a single 0–1 drive value. Each Controllable that uses this pattern holds a configurable dict of `{field_name: weight}` pairs, computes a weighted sum, normalises, and EMA-smooths the result each frame. New fields can be added to the bag via config without code changes. Not all Controllables need a Signal Bag — some may respond to individual fields directly (e.g. `captcha_blowup` triggering a one-shot effect).

**Show Network**:
The isolated Ethernet LAN that connects all show computers during installation. All OSC communication travels over the Show Network. Internet uplink deliberately omitted to keep the network simple and stable.

**Show Dashboard**:
A browser-based monitoring interface accessible on the Show Network. Operator connects their laptop to the Show Network to access it. Custom pages per Element, fed by each Element's FastAPI/WebSocket server (the same `get_state()` snapshots that Controllables already produce). No internet access required.

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

# The Community Garden

A touring interactive installation that puts visitors inside a world of systems — natural, technological, bureaucratic, and social — and lets them feel those systems respond to their presence.

This file is the glossary: what each word means, so code and docs use one name per thing. Addresses, settings, field lists and which file holds what live with the code and in each Element's doc (`docs/<Element>.md`).

## The installation

**The Community Garden**:
The name of the full interactive experience. Contains four Elements that can operate independently or together in a shared physical space.
_Avoid_: "the show", "the project", "the system"

**Element**:
One of the four self-contained interactive components: FlowerBeds, TreeHouse, Playing the Pipes, FundingCAPTCHA. Each has its own show-control software, hardware and thematic intent, and can exchange OSC messages with the others.
_Avoid_: "system", "module", "component", "installation" (for a single Element)

**Visitor**:
A person experiencing The Community Garden. They interact physically with the space and the Elements in it.
_Avoid_: "user", "audience", "player" (except within FundingCAPTCHA)

**Hub**:
The TreeHouse's role: it receives signals from the other Elements and reflects the garden's aggregate activity.
_Avoid_: "controller", "master", "server"

**Garden State**:
The live signals from all Elements plus the operator's Show Mode and brightness. The TreeHouse collects them and passes a snapshot to every Controllable and location controller. It holds raw per-Element values, not an aggregate; each receiver weighs them itself.

**Show Mode**:
The operator's setting for the TreeHouse: `active`, `dim` or `inactive`. A Garden State field.
_Avoid_: using "show mode" for anything in FundingCAPTCHA

## Elements

**FlowerBeds**:
The Element at the entrance. Servo-driven flowers with mirrors at their centres track Visitors using depth-camera blob detection. Thematic intent: surveillance and self-image — the flowers follow you, and show you yourself being followed.

**TreeHouse**:
The centrepiece Element and the Hub. A 9.5-foot structure (3-foot base + house), hyper-realistic outside and otherworldly inside. Visitors peer in through plexiglass windows; one front door opens so they can reach into a diorama. Branches on the roof grow and wither with Garden State.

**Playing the Pipes**:
The Element growing out of the base of the TreeHouse — a Dr. Seuss/Rube Goldberg tangle of water pipes and electrical conduit fitted with controls. Visitors steer a music system (granulators, loop players) by operating them. Thematic intent: the literal flow of utilities through infrastructure, and the figurative flow of money and influence through society.
_Avoid_: "playing music", "triggering notes" — Visitors *steer* the music

**FundingCAPTCHA**:
The Element opposite Playing the Pipes. A 7-foot kiosk styled as a CRT monitor. A short-throw projector lights the Screen; a depth camera on the kiosk faces the Players and captures their silhouettes, which activate cells on a projected grid. Thematic intent: the frustration and irony of humans proving their humanity to robots, and the fear of handing control to systems that may malfunction with no recourse.

## FundingCAPTCHA

**Screen**:
The vertical projection surface on the front of the kiosk. Shows game content and the Players' live silhouettes. Players stand in front of it; they do not touch it.
_Avoid_: "touch screen", "canvas", "display"

**Player**:
A Visitor standing in the Play Zone. FundingCAPTCHA is the only Element where "Player" is right; elsewhere use Visitor. Play is drop-in/drop-out.

**Arc**:
One Player run of one Game. Difficulty ramps as Players succeed, and the Arc always ends in a Blow-Up; beating a Level only raises the difficulty. Every Game must guarantee a loss when Players stop interacting (ADR-0003).
_Avoid_: "session", "run", "level" (a Level is one stage within an Arc)

**Blow-Up**:
The spectacular end-of-Arc failure. Deliberately rewarding, so that failing after a long Arc feels like a payoff. After it the kiosk returns to the Screensaver.

**Screensaver**:
What the kiosk shows between Arcs. It never interrupts an Arc. A Player who stays in the Play Zone long enough starts a new Arc.
_Avoid_: "attract screen", "idle animation", "lobby"

**Game**:
A set of mechanics paired with a Level set. Today the only Game is BodyCaptcha. Each Arc plays one Game, picked by shuffle bag.
_Avoid_: "game type", "mode"

**Level**:
One authored puzzle within a Game. For BodyCaptcha: a prompt, an image, a grid size, the cells the Player must cover, and a designer-assigned difficulty of 1–5. An Arc draws Levels by shuffle bag from those at the same difficulty as the last one beaten or one step harder.
_Avoid_: "round", "stage", "difficulty step"

**Body Grid**:
The input layer that maps Players' silhouettes to a grid of on/off cells. A cell turns on when enough of its pixels are foreground inside a Depth Slab. It belongs to no one Game.
_Avoid_: conflating Body Grid with BodyCaptcha — Body Grid is the input layer; BodyCaptcha is a Game that uses it

**Play Zone**:
The depth ranges in front of the camera where a Player's pixels count, given as one or more Depth Slabs. Pixels outside every slab are holes in the silhouette, including anything nearer than the nearest slab.
_Avoid_: "detection zone", "active area"

**Depth Slab**:
One depth band, from a near to a far distance, with its own id.
_Avoid_: "depth layer", "depth band"

**Intensity**:
A 0–1 value FundingCAPTCHA reports to the TreeHouse: how far the Arc has got toward its Blow-Up, and 0 between Arcs. During an Arc, a weighted sum of difficulty and time pressure.
_Avoid_: "difficulty", "score", "engagement level"

**Blow-Up Signal**:
The one-shot message FundingCAPTCHA sends the TreeHouse when a Blow-Up happens. An event, not a value.

**Blow-Up Reaction**:
What the TreeHouse does on a Blow-Up Signal. The Branches recoil. In the location controller firmware, a channel spikes to full and decays; that part is off while the controllers ignore Garden State (ADR-0021).

**Setup**:
One Shadertoy-style shader piece for the Screen: a folder holding its GLSL tabs and its settings.
_Avoid_: "shader" (a Setup is several), "scene" (that is a Looking Glass term)

**Body**:
What a Setup sees of the people in front of the kiosk: a texture where red is presence and green is nearness. On the kiosk it comes from the depth camera; in Shadertoy, from a mouse-painted stand-in.
_Avoid_: "silhouette" for the shader input, "mask"

**Playlist**:
What the kiosk plays in place of the Game Arc: Setups and videos in one shuffle bag.

## FlowerBeds

**FlowerCluster**:
One servo motor at a fixed world position, turning a group of flowers. Each frame it picks a Visitor to look at and returns a motor command.

**Attraction**:
The policy that decides which Visitor a FlowerCluster looks at: a weighted score of proximity, Dwell and Inertia. The tuning values and the scoring live together in it.
_Avoid_: "AttractionConfig", "attraction config", "scoring weights"

**Dwell**:
How many consecutive frames a Visitor has been within one FlowerCluster's influence radius. Counted per cluster (ADR-0002).

**Inertia**:
The bonus for the Visitor a FlowerCluster looked at last frame. Stops it flicking between Visitors at similar distances.

## TreeHouse

**Location**:
A part of the TreeHouse lit by its own ESP32-S3 location controller (ADR-0020). There are five. Each controller animates its own lights; the Pi sends it Garden State, which it ignores for now (ADR-0021).
_Avoid_: naming lights by Pico or channel

The five Locations:
- **Swannatopia**: a fireplace, an overhead light and a chandelier.
- **Julia**: a string of 12 V LED filaments, dimmed on a slow random walk.
- **Jess**: two colour strips with the rave look, plus a very bright strobe.
- **Dormer**: the dormer at the top of the structure; one slowly breathing glow.
- **Garage**: the welding effect, an arc flash and glowing pixels behind the garage's frosted windows.

**Diorama**:
A self-contained miniature room seen through a TreeHouse window.

**Club**:
The rave diorama. Holds the Club screen, a small display showing rotating messages (ADR-0017).

**Looking Glass**:
The TreeHouse's shader display. It shows one scene at a time: `bloom`, `fractal`, `mycelium` or `cosmos`.

**Controllable**:
Anything the TreeHouse Pi drives from Garden State each frame. Two exist: the Looking Glass and the Branches. The LEDs are not Controllables; the location controllers own them.
_Avoid_: "Display"

**Branch**:
A motorised branch on the TreeHouse roof. A Dynamixel servo drives a lead screw that pushes a wire of leaves out of a housing dressed as a tree branch, so the Branch extends or withers. How many there are is a setting.
_Avoid_: "arm", "limb", "antenna"

**Signal Bag**:
A firmware term. In the location controller firmware, each channel's weights over the Garden State fields, reduced to one 0–1 drive level. Inert while the controllers ignore Garden State (ADR-0021).

## Playing the Pipes

**Tiller Control**:
The control metaphor. Visitors steer the music like a boat: the controls change its direction and character, and do not trigger notes.
_Avoid_: "playing", "triggering", "note input"

## Shared

**IIVision**:
The shared computer-vision library: depth camera, background models, blob detection, blob stabilisation, coordinate transforms. FlowerBeds uses the whole pipeline. FundingCAPTCHA uses the camera and a background model for silhouettes, and blob stabilisation for the Playlist's blob tracking.

**Blob**:
One detected person, found by depth background subtraction and connected regions.

**Blob Track**:
A Blob followed across frames with a stable identity and a smoothed position.

**OSC Fabric**:
The OSC-over-UDP messages between Elements. Any Element may send to any other; the TreeHouse is the main receiver. Every address is in [`docs/osc-fabric.md`](docs/osc-fabric.md).

**Show Network**:
The isolated LAN that joins the show computers and controllers: Ethernet, plus WiFi for the location controllers. It has no internet uplink, by design.

**Show Dashboard**:
The browser monitoring pages an operator opens from a laptop on the Show Network, one page per Element.

## Flagged ambiguities

- "module" has two meanings: a `FlowerModule` in FlowerBeds code (a physical group of FlowerClusters), and loosely "one of the four parts of the show". Use **Element** for the second.
- "bloom" is a Looking Glass scene. It is not a value for how far the Branches are extended; nothing in the code has one.

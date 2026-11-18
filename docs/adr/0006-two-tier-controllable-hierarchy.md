# ADR 0006 — Two-tier Controllable hierarchy (Controllable / LEDControllable)

**Status:** Accepted and amended by [ADR-0020](0020-treehouse-esp32s3-location-controllers.md)

*Note, 2026-11-18: only the first tier remains. The per-room classes were never built, and `LEDControllable` and `PicoDriver` were removed on 2026-11-11 (#192) when the LEDs moved to the location controllers (ADR-0020). `Controllable` (`ShowControl/TreeHouse/controllables/base.py`) has two subclasses: `BranchController` and `LookingGlassControllable`.*

## Context

The TreeHouse controls heterogeneous outputs: LED strips, Dynamixel branch motors, and a video renderer. The original `Display` abstraction assumed everything produced pixel data (`get_frames()`), which forced non-LED outputs (Looking Glass, branch motors) to return empty lists — a leaky abstraction.

Additionally, each physical room/space has distinct Garden-State-reactive animation behaviour that cannot be expressed through config alone, making a single generic `LEDDisplay` class insufficient.

## Decision

Replace the flat `Display` list with a two-tier hierarchy:

- **`Controllable`** (base): `update(dt, state: GardenState)` + `get_state()`. Every controlled output inherits from this.
- **`LEDControllable(Controllable)`** (subclass): adds `get_pixels() → list[ChannelFrame]`. Only LED-driving outputs inherit this.

Each physical room/space is its own `LEDControllable` subclass with bespoke animation logic. Non-LED outputs (`BranchController`, `LookingGlassDisplay`) inherit directly from `Controllable` and own their output hardware internally.

The `PicoDriver` aggregates pixels from all `LEDControllable` instances each frame. The `Coordinator` calls `update()` on all `Controllable` instances uniformly.

## Reasons

- Removes the hollow `get_frames() → []` pattern from non-LED outputs.
- Gives each room a natural home for its own reactive animation logic.
- `get_pixels()` has a clear, justified purpose: aggregation by PicoDriver.
- `BranchController` and `LookingGlassDisplay` drive their own hardware inside `update()` — the Coordinator needs no motor- or video-specific methods.

## Consequences

- `displays/base.py` needs to be refactored: `Display` → `Controllable`, `get_frames()` → `get_pixels()` on new `LEDControllable`.
- Each room becomes its own class (e.g. `HouseSwarmingDisplay`, `ClubDisplay`, `AtticDisplay`). More files, but each is small and self-contained.
- `coordinator.py` splits its display list into `list[Controllable]` (all) and filters `list[LEDControllable]` for pixel aggregation.

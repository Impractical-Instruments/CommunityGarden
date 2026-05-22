# ADR 0008 — GardenState → display expression mapping

**Status:** Accepted

## Context

`GardenState` carries four incoming signals from across the installation — `flowerbeds_activity`, `captcha_intensity`, `captcha_blowup`, and `pipes_activity` — but nothing in any `update()` method uses them to change a display. The wiring exists; the reactive logic does not.

This ADR decides the personality of each TreeHouse display: how it reads and responds to the full GardenState each frame.

## Design principle

Every display receives the full `GardenState` and decides for itself how to aggregate and respond to the signals. There is no central routing of "signal X goes to display Y." This lets each display have a distinct personality and allows fine-grained tuning without architectural changes.

## Decision

### Branches

**Personality: hopeful responder.**

Branch extension is driven by a weighted sum of all four signals, with `flowerbeds_activity` weighted highest (people = life). When the garden is active, branches reach outward; when it goes quiet, they wither back. A `captcha_blowup` event triggers a visible startle/recoil before settling back to the weighted position.

Signal weights and max/min extension angles are configurable in `settings.json`.

### ForgeAndFlora

**Personality: pipes-led with intensity riders.**

- `pipes_activity` → blend target (0.0 = welding arc, 1.0 = magical gardening bloom)
- `captcha_intensity` + `flowerbeds_activity` combined → flicker/animation dynamic range and speed (both how dramatic the arc flicker is and how vivid the bloom pulse is)

The Forge expresses whether the infrastructure is being played (music flowing = bloom) while the intensity of everything happening in the garden makes the effect more or less dramatic.

### LookingGlass

**Personality: garden mood mirror.**

Scene selection follows a priority-ordered rule (highest priority first):

| Condition | Scene |
|---|---|
| `captcha_blowup` fired | `overload` (hold for configurable duration, then return) |
| High `captcha_intensity`, low other signals | `cosmos` — cold, detached, humanity failing the machine |
| High `captcha_intensity` | `fractal` — recursive, mathematical, frustrating |
| High `flowerbeds_activity` | `mycelium` — branching, connective, people finding each other |
| Otherwise | `bloom` — organic, slow, hopeful |

Speed tracks a weighted sum of all four signals.

`overload` is a new fifth scene: rapid cycling through the four existing scenes with static flashes between them. It is fired as a reward when `captcha_blowup` occurs and holds for a configurable duration before mood-mirror logic resumes.

`LookingGlass.SCENES` is updated from `("bloom", "fractal", "mycelium", "cosmos")` to include `"overload"`.

### Dioramas, dormer, attic (all `LEDDisplay`)

**Personality: config-driven shared logic.**

A single `GardenStateResponse` config block per display in `settings.json` specifies per-signal weights. The shared logic drives all three axes:

- **Pattern selection** — signal weights map to pattern choices (e.g. quiet → `incandescent`, active → `breathe`/`chase`, blowup → `strobe`)
- **Brightness** — overall activity scales brightness up from a configurable idle floor
- **Animation speed** — for time-based patterns (`breathe`, `mycelium`), speed tracks the weighted signal sum

This allows each display to have a distinct personality tunable in config without writing new subclasses.

### Porch lights

**Personality: blowup-only.**

Existing behaviour is unchanged and complete:
- Normal: warm incandescent glow
- `captcha_blowup` → sickly blue flicker (`blowup_duration` seconds)
- Aftermath: dim orange smoulder (`aftermath_duration` seconds) → fade back to normal

The porch lights are the front door; their story is purely the CAPTCHA moment. Other signals are intentionally ignored.

## Reasons

- Giving each display full GardenState access preserves the option to tune personality without architectural changes — just update the display's `update()` or its config weights.
- Config-driven weights for the generic LEDDisplays avoid a proliferation of nearly-identical subclasses.
- Keeping the porch lights blowup-only preserves the clarity of that moment; mixing in other signals would dilute it.
- The `overload` scene is defined at the schema level (a named scene string) so the video renderer can implement it independently of the Python control side.

## Consequences

- `BranchController.update()` must compute a weighted blend of all four signals to a target position each frame.
- `ForgeAndFloraDisplay.update()` must read `pipes_activity` for blend target and `captcha_intensity` + `flowerbeds_activity` for animation intensity instead of relying on `set_blend()` / `set_mode()` calls from the Coordinator.
- `LookingGlassDisplay.update()` must implement scene selection logic and track blowup state internally. `SCENES` gains `"overload"`.
- `LEDDisplay` or a subclass gains a `GardenStateResponse` config struct and reactive `update()` logic.
- Signal weights and thresholds for all displays must be added to `settings.json` and documented.
- The video renderer must implement the `overload` scene (rapid cycling + static flashes).

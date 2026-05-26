# ADR 0017 — Club Diorama Rave Screen

**Status:** Accepted

## Context

The Club diorama depicts a 90s Detroit rave scene. It currently has 20 SK6812 LEDs (chase pattern) driven by Pico A. The DJ booth inside the diorama has physical space for a small screen. We want animated, readable content on that screen to reinforce the rave theme.

## Decision

Add a 5" HDMI LCD (800×480) mounted in the DJ booth of the Club diorama. A standalone pygame app running on the TreeHouse Pi renders rotating text messages with a rave-era visual aesthetic.

### Hardware

- **Screen:** 5" mini-HDMI LCD, 800×480, capacitive touch not used
- **Connection:** HDMI from TreeHouse Pi (currently 2GB; upgrade to 8GB if resource contention with LookingGlass renderer)
- **Mount:** Inside Club diorama, DJ booth position

### Software

Standalone pygame app (`treehouse/club_screen.py`):

- Reads messages from `treehouse/club_messages.txt` (versioned in GitHub)
- One message per line-break-delimited block; blank line = message separator
- Rotates through messages on a configurable timer (default 10s, `settings.json` key `club_screen.interval_seconds`)
- Reloads message file on each rotation — no restart needed to update messages
- Renders full-screen (800×480), black background
- Visual style: 90s rave aesthetic — bright accent color, bold font, scanline overlay pass
- No OSC / GardenState integration; fully standalone

### Message file format

```
ACID HOUSE FOREVER

NO SLEEP TIL DETROIT

THE MUSIC IS THE MESSAGE
```

Each non-empty line block is one message. File path configurable via `settings.json` key `club_screen.messages_file`.

### Scanline effect

Drawn as a pygame surface overlay: semi-transparent horizontal lines every 2px, alpha ~40. Rendered on top of each frame. No external shader dependency — pure pygame.

### Process management

Launched as a subprocess by `main.py` alongside the LookingGlass renderer subprocess (see ADR-0018 pattern). If TreeHouse Pi cannot sustain both, move club screen to a spare 8GB Pi.

## Reasons

- pygame already used project-wide; keeps the stack uniform and enables future shader effects if needed
- Standalone loop (no OSC) — Club screen has no reactive story to tell, simplicity wins
- File-based messages versioned in GitHub — content updates without code deploys
- Hot-reload on rotation — update the file, next message cycle picks it up
- ADR-0018 subprocess pattern already established for video rendering on the TreeHouse Pi

## Consequences

- `treehouse/club_screen.py` — new pygame app
- `treehouse/club_messages.txt` — initial message set, versioned
- `settings.json` gains `club_screen.interval_seconds` and `club_screen.messages_file`
- `main.py` launches club screen subprocess (mirrors LookingGlass pattern)
- If 2GB Pi can't run both subprocesses, assign club screen to a spare 8GB Pi and update `docs/TreeHouse.md`

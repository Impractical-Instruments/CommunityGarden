# Conventions

Each Element's files are listed in its doc (`docs/<Element>.md`); the shared vision library's in [`IIVision/README.md`](../../IIVision/README.md).

## Coordinate system

**World space** (installation frame): **X=right, Y=forward, Z=up, centimetres** — right-handed.

**Camera space** (Orbbec native): **X=right, Y=down, Z=forward, metres**.

`IIVision.transforms.orbbec_to_world()` converts camera → world (`world_pos_cm` is the resulting field on `TrackedBlob`):
- World X ← Camera X
- World Y ← Camera Z
- World Z ← −Camera Y

Never pass camera-space values to anything that expects world space.

## Rotation convention

`Rotator` stores pitch/yaw/roll in degrees, applied intrinsically Roll → Pitch → Yaw:

- **Pitch** — around X (right); positive = nose up
- **Yaw** — around Z (up); positive = forward toward right
- **Roll** — around Y (forward)

Yaw 0° = facing +Y (forward). Yaw 90° = facing +X (right).

Positive yaw is clockwise seen from above, the opposite of the right-handed rule, so `rotator_to_matrix()` negates yaw before building the matrix. Go through it; do not build a rotation from a `Rotator` by hand.

## Logging

Show code logs through `logging`, with one logger name per program so `journalctl` lines say where they came from:

| Program | Logger name |
|---|---|
| FlowerBeds | `flower_beds` |
| TreeHouse | `treehouse`; its subprocesses use `looking_glass` and `club_screen` |
| FundingCAPTCHA kiosk | `captcha`, with children such as `captcha.camera` and `captcha.monitor` |
| FundingCAPTCHA playlist player | the module's name: `playlist_app`, `shader_stage`, `shadertoy`, `video_player` |
| Playing the Pipes | `pipes-bridge`, `pipes-health` |
| Dashboard | `dashboard` |
| OSCFabric | `osc_fabric` |
| IIVision | `logging.getLogger(__name__)` |

```python
import logging
log = logging.getLogger("flower_beds")
```

- **Show loops and libraries never `print`.** Use `log.info`, `log.warning`, `log.error`.
- **Tools a person starts by hand may `print` what that person needs at the terminal**, such as the URL to open. Today: the layout tool, the FlowerBeds visualizer, the Dashboard and Pipes health servers, the BodyCaptcha editor, and the scripts under `scripts/`.

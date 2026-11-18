# Python Conventions

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

## Logging

```python
import logging
log = logging.getLogger("flower_beds")
```

Use `log.info`, `log.warning`, `log.error` throughout — never `print`.

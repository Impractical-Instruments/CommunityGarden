# Python Conventions

## Module responsibilities — FlowerBeds

| File | Responsibility |
|---|---|
| `ShowControl/FlowerBeds/main.py` | Argument parsing, config loading, main frame loop, wiring IIVision + Coordinator + OSC + visualizer |
| `ShowControl/FlowerBeds/flower_beds.py` | `Coordinator`, `FlowerModule`, `FlowerCluster`, `Attraction` — cluster assignment and yaw calculation |
| `ShowControl/FlowerBeds/visualizer.py` | FastAPI WebSocket server; `broadcast(state)` called each frame |
| `ShowControl/FlowerBeds/layout_tool.py` | Browser GUI for placing modules and aiming clusters (ADR-0015) — run on operator laptop, not the show Pi |

Blob detection, stabilisation, camera abstraction, and coordinate transforms all live in `IIVision/`. See [architecture](architecture.md).

## Coordinate system

**World space** (installation frame): **X=right, Y=forward, Z=up, centimetres** — right-handed.

**Camera space** (Orbbec native): **X=right, Y=down, Z=forward, metres**.

`Blob3D.world_pos_cm()` converts camera → world:
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

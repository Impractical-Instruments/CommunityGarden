# Configuration Reference

## settings.json (per Element)

Each Element has its own `settings.json`. FlowerBeds example:

```json
{
  "calibration_frames": 60,

  "stabilizer": {
    "max_match_dist_cm": 80.0,
    "smoothing_alpha": 0.3,
    "max_miss_frames": 8,
    "min_confirm_frames": 2
  },

  "coordinator": {
    "exclusion_radius_cm": 40.0,
    "attraction": {
      "influence_radius_cm": 300.0,
      "distance_weight": 1.0,
      "distance_falloff_cm": 150.0,
      "dwell_weight": 0.5,
      "dwell_halflife_frames": 30,
      "inertia_weight": 0.3
    },
    "modules": [
      {
        "name": "Module 1",
        "registration_point_cm": [100.0, -200.0, 0.0],
        "rotation": {"pitch": 0, "yaw": 0, "roll": 0},
        "clusters": [
          {
            "motor_id": 1,
            "pos_offset_cm": [40.0, -30.0, 0.0],
            "rotation_offset": {"pitch": 0, "yaw": 0, "roll": 0}
          },
          {
            "motor_id": 2,
            "pos_offset_cm": [40.0, -75.0, 0.0],
            "rotation_offset": {"pitch": 0, "yaw": 0, "roll": 0}
          },
          {
            "motor_id": 3,
            "pos_offset_cm": [100.0, -25.0, 0.0],
            "rotation_offset": {"pitch": 0, "yaw": 0, "roll": 0}
          },
          {
            "motor_id": 4,
            "pos_offset_cm": [95.0, -70.0, 0.0],
            "rotation_offset": {"pitch": 0, "yaw": 0, "roll": 0}
          }
        ]
      }
    ]
  },

  "cameras": [
    {
      "name": "Camera",
      "pos_cm": [0.0, 0.0, 275.0],
      "rotation": {"pitch": -90.0, "yaw": 0.0, "roll": 180.0},
      "serial": "CPCG85300095",
      "width": 640,
      "height": 400,
      "framerate": 10
    }
  ]
}
```

- `name` — human-readable module label (shown in layout tool, not used by show logic).
- `motor_id` — must match the Dynamixel servo ID burned in via `Dynamixel_Config` firmware. Default sequential IDs (1–48) are placeholders; always override before show.
- `serial` — Orbbec device serial. Leave empty to use the first detected camera.
- `registration_point_cm` — physical anchor of the module in world space `[X_right, Y_forward, Z_up]` cm. Edit via the layout tool (`python layout_tool.py`), not by hand.
- `pos_offset_cm` — cluster position relative to module registration point, same coordinate convention.
- All position vectors use **[X_right, Y_forward, Z_up]** in centimetres.

### Editing module layout

Use the layout tool on your Windows laptop — do not hand-edit `registration_point_cm` or yaw values:

```
cd ShowControl/FlowerBeds
python layout_tool.py
# opens http://localhost:8764
```

The tool writes only `coordinator.modules[]` and backs up `settings.json.bak` before saving. See ADR-0015.

## network.json — single source of truth for all addresses

`ShowControl/network.json` holds every IP, MAC, and port for the entire installation. No source file or firmware may hardcode a network address.

```json
{
  "heartbeat_interval_s": 5,
  "elements": {
    "treehouse":  { "ip": "192.168.1.10", "osc_port": 9001, "http_port": 8766 },
    "flowerbeds": { "ip": "192.168.1.11", "osc_port": 9002, "http_port": 8765 },
    "captcha":    { "ip": "192.168.1.12", "osc_port": 9003, "http_port": 8080 },
    "pipes":      { "ip": "192.168.1.13", "osc_port": 9004, "http_port": 8767 }
  },
  "firmware": {
    "flowerbeds_controller_1": { "ip": "192.168.1.50", "mac": "DE:AD:BE:EF:15:00", "osc_port": 9000 },
    "flowerbeds_controller_2": { "ip": "192.168.1.51", "mac": "DE:AD:BE:EF:15:01", "osc_port": 9000 },
    "treehouse_branch":        { "ip": null, "mac": null, "osc_port": null }
  }
}
```

Firmware reads addresses from a generated `config.h` produced by `scripts/hooks/firmware_config_gen.py` before each flash. The TreeHouse branch controller uses USB serial and has no IP/MAC (see ADR-0005).

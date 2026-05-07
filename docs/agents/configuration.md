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

  "modules": [
    {
      "registration_point_cm": [100.0, -200.0, 0.0],
      "rotation": {"pitch": 0, "yaw": 0, "roll": 0},
      "clusters": [
        {
          "motor_id": 1,
          "pos_offset_cm": [40.0, 0.0, 0.0],
          "rotation_offset": {"pitch": 0, "yaw": 0, "roll": 0}
        }
      ]
    }
  ],

  "cameras": [
    {
      "name": "Entrance",
      "pos_cm": [0.0, -300.0, 200.0],
      "rotation": {"pitch": -30.0, "yaw": 0.0, "roll": 0.0},
      "serial": "CPCG853000CB",
      "width": 640,
      "height": 400,
      "framerate": 10
    }
  ]
}
```

- `motor_id` — must match the Dynamixel servo ID set via `Dynamixel_Config` firmware.
- `serial` — Orbbec device serial. Leave empty to use the first detected camera.
- `registration_point_cm` — physical anchor of the module in world space [X_right, Y_forward, Z_up] cm.
- All position vectors use **[X_right, Y_forward, Z_up]** in centimetres.

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

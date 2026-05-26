# The Community Garden
Show systems for [Connect Beyond Festival](https://www.connectbeyondfestival.com/)

![Master View](https://github.com/user-attachments/assets/577685e8-6b0c-4230-9f48-d12ddde26143)

---

## Docs

- **[bootstrap.md](docs/bootstrap.md)** — one-time hardware provisioning (fresh Pis, Windows host, operator laptop)
- **[showtime.md](docs/showtime.md)** — install, start, debug, maintain — daily + venue ops, deploy, troubleshooting
- Per-Element detail: [FlowerBeds](docs/FlowerBeds.md) · [TreeHouse](docs/TreeHouse.md) · [FundingCAPTCHA](docs/FundingCAPTCHA.md) · [PlayingThePipes](docs/PlayingThePipes.md) · [Dashboard](docs/Dashboard.md)

---

## What's here

| Element | Description |
|---|---|
| **FlowerBeds** | Servo-driven flowers that follow visitors (depth camera → OSC → Dynamixel) |
| **TreeHouse** | LED + video effects in a diorama dollhouse structure (Hub for the OSC Fabric) |
| **FundingCAPTCHA** | Pygame kiosk where Players activate a projected grid with body silhouettes |
| **Playing the Pipes** | Max/RNBO music system steered by rotary encoders on physical valves/switches |

The **Show Dashboard** (browser UI for monitoring and mode control) runs on the TreeHouse machine — see [docs/Dashboard.md](docs/Dashboard.md).

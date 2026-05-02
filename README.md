# The Community Garden
Show systems for [Connect Beyond Festival](https://www.connectbeyondfestival.com/)

![Master View](https://github.com/user-attachments/assets/577685e8-6b0c-4230-9f48-d12ddde26143)

---

## What's here

| Element | Description |
|---|---|
| **FlowerBeds** | Servo-driven flowers that follow visitors (depth camera → OSC → Dynamixel) |
| **Tree House** | LED + video effects in a diorama dollhouse structure |
| **FundingCAPTCHA** | Browser-based proof-of-humanity kiosk game suite |
| **Dashboard** | Web UI for monitoring and controlling all elements |

---

## Prerequisites

- Python 3.11+
- Git

Each show element has its own `requirements.txt`. Install them separately — they don't share a virtualenv.

---

## Starting the show

Run each element from its own terminal. All elements are independent; start only what you need.

### Dashboard
```bash
cd ShowControl/Dashboard
python serve.py
# → http://<your-ip>:9000
```

### Tree House
```bash
cd ShowControl/TreeHouse
pip install -r requirements.txt
python main.py
```

### FlowerBeds
```bash
cd ShowControl/FlowerBeds
pip install -r requirements.txt
python main.py --config settings.json
```

### FundingCAPTCHA
```bash
cd ShowControl/FundingCAPTCHA
python server.py
```

---

## Running without hardware

Every element has a dev mode — no camera, no LEDs, no servos required.

| Element | Dev flag(s) |
|---|---|
| Tree House | `--no-pico` |
| FlowerBeds | `--mock --no-osc` |
| FundingCAPTCHA | `--mock-camera` |

Example:
```bash
python main.py --no-pico                    # Tree House, no Pico
python main.py --mock --no-osc              # FlowerBeds, no camera or servos
python server.py --mock-camera              # FundingCAPTCHA, no depth camera
```

---

## Dashboard

Open `http://<show-computer-ip>:9000` from any browser on the same network. The dashboard auto-detects which elements are online.

From the **Tree House** detail page you can monitor all displays live and trigger any state — show modes, LED patterns, Looking Glass scenes, Forge & Flora, Porch Lights blowup — without touching a terminal.

---

## Ports

| Service | Port |
|---|---|
| Dashboard | 9000 |
| FlowerBeds visualizer | 8765 |
| Tree House visualizer | 8766 |
| FundingCAPTCHA | 8080 |
| OSC listen (Tree House) | 9001 |

All devices must be on the same LAN. The dashboard server prints its local IP on startup.

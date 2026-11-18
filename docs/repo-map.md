# Repo map

Every tracked directory down to the level where its own README takes over. Start at that README where one is linked.

```
CommunityGarden/
├── IIVision/                               Shared depth-camera vision package              → IIVision/README.md
├── ShowControl/                            Show-control software, one directory per Element → ShowControl/README.md
│   ├── FlowerBeds/                         Depth camera to servo flowers                   → docs/FlowerBeds.md
│   ├── TreeHouse/                          The Hub: Garden State, Looking Glass, Branches  → docs/TreeHouse.md
│   ├── FundingCAPTCHA/                     The kiosk game                                  → docs/FundingCAPTCHA.md
│   ├── PlayingThePipes/                    Music engine (Max, moving to reuben) and bridge → its README.md
│   ├── Dashboard/                          Browser monitoring pages                        → docs/Dashboard.md
│   ├── OSCFabric/                          Shared package: Element signals to the TreeHouse → its README.md
│   ├── ShowWeb/                            Shared package: LiveServer behind the visualizers
│   └── network.json                        Every IP, MAC and port on the Show Network
├── Firmware/                               One directory per microcontroller program       → Firmware/README.md
│   ├── FlowerBeds_Follow_ServoController/  OpenRB-150, Arduino: FlowerBeds servos          → its README.md
│   ├── TreeHouse_Controllers/              ESP32-S3, PlatformIO: every TreeHouse LED       → its README.md
│   ├── TreeHouse_BranchController/         OpenRB-150, Arduino: TreeHouse Branch servos    → its README.md
│   └── PlayingThePipes_EncoderPico/        Pi Pico, MicroPython: rotary encoders           → its README.md
├── scripts/                                Deploy, install and repo tooling                → scripts/README.md
│   ├── git-hooks/                          The pre-commit hook that blocks private show content
│   ├── hooks/                              firmware_config_gen.py: network.json to firmware headers
│   └── lib/                                install-element.sh, sourced by each Element's installer
├── vendor/
│   └── reuben/                             Git submodule: the reuben audio engine (needs Rust to build)
├── docs/
│   ├── adr/                                Architecture Decision Records
│   ├── agents/                             Agent guidance, indexed from AGENTS.md
│   ├── audit/                              The 2026-11-09 codebase audit and its backlog
│   ├── fabrication/                        Build notes for physical pieces
│   ├── bootstrap.md, showtime.md           Operator docs: first install; running a show
│   └── <Element>.md                        One operator reference per Element
├── .github/
│   ├── workflows/                          CI: tests.yml, testmon-data.yml, claude.yml
│   └── scripts/                            What the workflows call: path filter, shader tests, reuben pin check
├── AGENTS.md                               Agent entry point: test commands and critical constraints
├── CONTEXT.md                              Domain glossary; read before naming anything
├── Makefile                                setup, test, test-fast, test-fundingcaptcha, test-firmware, validate-instruments
├── pyproject.toml                          The three packages, one extra per Element, pytest config
└── uv.lock                                 Locked dependencies; `make setup` builds .venv from it
```

There is no top-level `tests/` directory: tests sit beside the code as `test_*.py`.

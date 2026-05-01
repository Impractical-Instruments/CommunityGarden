# ADR 0005 — Branch controller uses USB serial, not Ethernet

**Status:** Accepted

## Context

The TreeHouse branch motors are driven by an OpenRB-150 running Dynamixel servos. The rest of the system (FlowerBeds) connects to its OpenRB-150 over Ethernet+OSC. The TreeHouse show-control computer (Raspberry Pi) sits physically 1–2 feet from the branch controller inside the structure.

## Decision

The branch controller communicates with the TreeHouse Pi over USB serial using the same JSON-lines protocol as the Pi Pico LED driver (`pico_driver.py`). No Ethernet hat is fitted to the branch OpenRB-150.

## Reasons

- Physical co-location makes USB the simplest and most reliable option — no network config, no IP address, no hat hardware.
- The Pi Pico LED driver already establishes the JSON-lines-over-USB-serial pattern in this codebase; reusing it keeps the TreeHouse internally consistent.
- Ethernet would only be justified if the controller needed to be physically remote from the Pi, which it does not.

## Consequences

- The branch controller is physically tethered to the TreeHouse Pi by USB. This is acceptable given co-location.
- If the controller is ever relocated (e.g., high in the structure beyond cable reach), swapping to Ethernet+OSC is straightforward — the OpenRB-150 firmware pattern already exists in the FlowerBeds firmware.
- The branch controller does **not** speak OSC; it speaks JSON lines. Keep this in mind if adding monitoring or TouchOSC manual control later.

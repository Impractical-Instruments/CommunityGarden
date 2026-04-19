# Glow Panel Prototypes

Two prototype approaches for mycelium-strand glow panels using SK6812 RGBW strips and 1/8" clear acrylic. Both panels are painted opaque, leaving only the mycelium strand shapes unmasked so light escapes only through those paths.

The firmware supports two gradient modes — run both on each panel and compare before committing to a method.

---

## Prototypes

| | [01 — Side-Lit Clear Acrylic](01_SideLit/README.md) | [02 — Back-Lit Frosted Acrylic](02_BackLit_Frosted/README.md) |
|---|---|---|
| **Light path** | Enters the acrylic edge, travels internally, exits through unmasked strand surfaces | Shines through the full panel face, frosting diffuses hotspots |
| **Acrylic prep** | None — use the clear 1/8" sheet as-is | Sand or film-frost one face before painting |
| **LED count (30×20cm proto)** | ~18 LEDs (single edge strip) | ~36–54 LEDs (2–3 rows behind panel) |
| **Gradient character** | Natural distance falloff from the lit edge; strands near the edge glow brightest | Uniform field; gradient is entirely software-controlled |
| **Hotspot risk** | Low — internal reflection softens point sources | Moderate — needs enough air gap and diffusion |
| **Paint masking side** | Top surface (the face you see) | Front face (same side as viewer) |
| **Best for** | Dramatic, directional, low-power | Even, controllable, full-panel coverage |

---

## Gradient Methods to Compare

Both panels run the same firmware (`firmware/panel_gradient.py`). Change `MODE` at the top of the file:

| Mode | Name | Character |
|---|---|---|
| `"A"` | Static gradient | Fixed brightness falloff from one end of the strip to the other. Calm, architectural. |
| `"B"` | Breathing gradient | Each LED pulses on a slightly offset sine wave. Organic, bioluminescent. |

Test both modes on both panels and note which combination reads best at festival viewing distance (~1–3 m).

---

## Shared Hardware

- Raspberry Pi Pico (MicroPython firmware)
- SK6812 RGBW strip, 60 LED/m density
- 5 V power supply (1 A covers up to ~60 LEDs at moderate brightness)
- Micro USB cable for flashing
- 300–470 Ω resistor on data line (prevents ringing)
- Small capacitor, 100–1000 µF across 5 V/GND at strip input (prevents voltage spike on power-on)

---

## Folder Layout

```
Prototypes/GlowPanels/
├── README.md                    ← you are here
├── 01_SideLit/
│   └── README.md                ← materials, build steps, wiring
├── 02_BackLit_Frosted/
│   └── README.md                ← materials, build steps, wiring
└── firmware/
    └── panel_gradient.py        ← MicroPython for Pico, both gradient modes
```

# Prototype 01 — Side-Lit Clear Acrylic

Light enters the acrylic from one edge and propagates internally via total internal reflection. The painted mycelium strands act as scattering points that break TIR and let light escape — so only the strand shapes glow. Strands far from the LED edge glow less intensely, giving a free, natural gradient.

---

## How It Works

```
  ┌──────────────────────────────────┐
  │   ░░░ painted opaque surface ░░░ │  ← black acrylic paint
  │                                  │
  │  ══ strand (clear, unpainted) ══ │  ← light scatters upward here
  │                                  │
  │   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
  └──────────────────────────────────┘
  ▲ LED strip along bottom edge
  Light travels right → gradient falls off naturally with distance
```

The gradient is physical: no software needed to create it. Mode B (breathing) adds organic animation on top.

---

## Materials

### Acrylic & Finishing
| Item | Spec | Notes |
|---|---|---|
| Clear acrylic sheet | 1/8" (3 mm), 30 × 20 cm | You already have this |
| Flat black acrylic paint | Liquitex Basics or similar | Matt finish prevents reflections |
| Small artist brush + sponge roller | — | Roller gives even opaque coverage |
| Mycelium stencil or frisket film | — | Mask strands before painting |
| Isopropyl alcohol, 70%+ | — | Degrease acrylic before painting |

### LED Strip & Electronics
| Item | Spec | Where to get |
|---|---|---|
| SK6812 RGBW strip | 60 LED/m, 5 V, white PCB preferred | Adafruit #2842 or BTF-Lighting |
| Strip segment length | 30 cm (≈ 18 LEDs) | Cut at solder pads |
| Raspberry Pi Pico | any revision | You already have this |
| 5 V / 1 A power supply | USB-A brick or bench supply | |
| 300 Ω resistor | 1/4 W | In-line on data wire |
| 470 µF capacitor | 6.3 V+ electrolytic | Across 5 V and GND at strip |
| Micro USB cable | — | For Pico programming |
| Hookup wire | 22–24 AWG stranded | ~30 cm of each colour |
| Heat-shrink tubing | 3 mm | Insulate solder joints |

### Enclosure & Mounting
| Item | Spec | Notes |
|---|---|---|
| Aluminium U-channel | 3/8" or 10 mm inner width, 30 cm | Holds strip + acrylic edge. Hardware store or online. |
| OR 3D-printed edge channel | See note below | PLA, black |
| Foam tape, 1 mm | — | Cushions acrylic in channel, diffuses LED hotspots |
| Black gaffer tape | — | Covers back of strip, seals channel ends |
| M3 screws + standoffs | 4× 10 mm | Mount panel to a test rig or frame |

> **U-channel alternative:** A folded strip of black craft foam taped along the edge works fine for a quick prototype. The goal is just to hold the strip flush against the acrylic edge and block light leakage from the sides.

---

## Build Steps

### 1. Cut and Degrease the Acrylic
- Cut acrylic to 30 × 20 cm if not already sized.
- Wipe all surfaces with IPA. Let dry 2 min.
- Leave the protective film on the back face during painting.

### 2. Mask the Mycelium Strands
- Sketch your strand pattern lightly in pencil on the **top surface**.
- Apply frisket/masking film and cut out the strand shapes with a craft knife, OR
- Use painters tape to rough-mask the strands (lower detail, easier).
- The unmasked areas will remain clear and glow.

### 3. Paint the Panel
- Apply 2–3 thin coats of flat black acrylic paint to the top surface using a sponge roller.
- Let each coat dry fully (15–20 min).
- Check over a light source: zero bleed-through between strands means you have enough coats.
- Carefully peel the masking once the final coat is dry.
- Peel the protective film from the back face.

### 4. Prepare the LED Strip
- Cut a 30 cm segment of SK6812 strip at the solder pads.
- Solder three wires: 5 V (red), GND (black), DATA (yellow/green).
- Solder the 300 Ω resistor in-line on the DATA wire, close to the strip end.
- Attach the 470 µF cap across 5 V/GND at the strip input solder pads (negative stripe = GND).
- Cover all solder joints with heat-shrink.

### 5. Mount Strip in Channel
- Stick the LED strip inside the U-channel with its self-adhesive backing, LEDs facing inward (toward where the acrylic edge will sit).
- Run a thin strip of 1 mm foam tape on the LED face — this presses the strip lightly against the acrylic edge and diffuses point-source hotspots.
- Slide the bottom edge of the acrylic into the channel. The acrylic edge should sit flush against (or 1–2 mm from) the LED faces.
- Seal the ends with black gaffer tape to prevent light escaping sideways.

### 6. Wire the Pico

```
SK6812 strip          Pico (MicroPython)
─────────────         ──────────────────
5 V           ──┬──→  VBUS  (pin 40)       [or external 5 V]
                │
470 µF cap ─ GND ──→  GND   (pin 38)
DATA      →[300Ω]──→  GP0   (pin 1)
```

> For strips longer than 30 LEDs or brighter colours, feed 5 V to the strip **directly from your PSU**, not through the Pico's VBUS. Connect GND of the PSU to Pico GND.

### 7. Load Firmware
1. Flash Pico with MicroPython if not already done (download UF2 from micropython.org, drag to RPI-RP2 drive).
2. Copy `../firmware/panel_gradient.py` to the Pico as `main.py` using Thonny or `mpremote`.
3. Set `NUM_LEDS = 18`, `MODE = "A"` for the first test.
4. Power up — strands should glow, bright at the bottom edge, fading toward the top.
5. Switch to `MODE = "B"` and re-run to compare the breathing effect.

---

## What to Observe

Stand 1–3 m back and note:

- **Gradient evenness** — does the falloff read as intentional or patchy?
- **Hotspot visibility** — can you see individual LED dots through the acrylic edge? (Foam tape should suppress this.)
- **Strand definition** — do the mycelium shapes read crisply or do they bloom/blur?
- **Colour** — adjust `COLOR_WARM` vs `COLOR_COOL` in the firmware to taste.
- **Mode A vs B** — static vs breathing at viewing distance.

---

## Tuning Tips

| Problem | Fix |
|---|---|
| Hotspots at edge | Add more foam tape thickness, or sand the bottom acrylic edge with 220-grit |
| Strands near top too dim | Increase `GRADIENT_MIN` in firmware, or add a second strip on the top edge |
| Paint bleeding under mask | Use thinner coats; press mask edges firmly before painting |
| Flickering | Add or increase the capacitor; check resistor on data line |
| Wrong colours | SK6812 byte order is GRBW on wire — see note in firmware |

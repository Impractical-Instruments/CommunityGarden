# Prototype 02 — Back-Lit Frosted Acrylic

SK6812 strips sit behind the acrylic in a shallow light box. The frosted face of the acrylic diffuses individual LED hotspots into a soft field. Opaque black paint on the front masks everything except the mycelium strands — those stay clear and glow wherever the light box illuminates them. The gradient is entirely software-driven, giving full control but requiring more LEDs than the side-lit approach.

---

## How It Works

```
  Viewer
    ↑
  ┌─────────────────────────────────┐
  │ ░░░ black paint (front face) ░░ │  ← opaque mask
  │ ══════ clear strand ══════════  │  ← glow escapes here
  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
  ├─────────────────────────────────┤  ← 1/8" frosted acrylic
  │   ≈ 3–5 cm air gap             │  ← lets light spread between LEDs
  │  ▓ SK6812 strip  ▓  strip  ▓   │  ← rows of strip on white base
  └─────────────────────────────────┘  ← white-painted MDF or foam-core backing
```

The air gap between the strips and the acrylic is critical — too shallow and you see stripe banding; too deep and the box gets bulky. 3–5 cm is the sweet spot for a 30 × 20 cm panel.

---

## Materials

### Acrylic & Finishing
| Item | Spec | Notes |
|---|---|---|
| Clear acrylic sheet | 1/8" (3 mm), 30 × 20 cm | You already have this |
| Frosted glass spray | Rust-Oleum 1903830 or similar | 2–3 light coats on **one face** — this becomes the back face |
| OR 220-grit sandpaper | — | Hand-sand one face to frost it; cheaper, slightly less even |
| Flat black acrylic paint | Liquitex Basics or similar | Applied to the **front face** |
| Frisket film or masking tape | — | Mask mycelium strands before painting |
| Isopropyl alcohol, 70%+ | — | Degrease before any coating |

> **Frosting tip:** Spray in thin passes 30 cm away. Two coats = light diffusion; three coats = heavier diffusion. More diffusion = softer glow but more light loss. Start light and add coats.

### LED Strip & Electronics
| Item | Spec | Where to get |
|---|---|---|
| SK6812 RGBW strip | 60 LED/m, 5 V | Adafruit #2842 or BTF-Lighting |
| Strip length | 90 cm total (3 × 30 cm rows) | Cut at solder pads |
| Raspberry Pi Pico | any revision | You already have this |
| 5 V / 2 A power supply | USB-A brick or bench PSU | 3 rows at moderate brightness needs ~1.5 A |
| 300 Ω resistor | 1/4 W | On data line |
| 470 µF capacitor | 6.3 V+ electrolytic | Across 5 V/GND at strip input |
| Micro USB cable | — | Pico programming |
| Hookup wire | 22–24 AWG stranded | ~60 cm each colour for daisy-chaining rows |
| Heat-shrink | 3 mm | |

### Light Box
| Item | Spec | Notes |
|---|---|---|
| Foam-core board | 5 mm, black exterior | Sides and back of the box. Craft stores, ~A1 sheet |
| OR MDF sheet | 6 mm | Sturdier; paint interior white |
| White acrylic paint or white foam-core | — | Coat the interior for maximum reflectivity |
| Hot glue gun + sticks | — | Assemble the box |
| Black gaffer tape | — | Seal seams, no light leakage |
| M3 screws + standoffs | 4× | Mount acrylic to box face |
| Self-adhesive hook-and-loop | — | Optional: keep acrylic removable for adjustments |

---

## Build Steps

### 1. Frost the Back Face of the Acrylic
Keep the protective film on the **front face**. Work on the bare back face.

**Spray method:**
- Lay the acrylic flat, back face up, outdoors or in ventilated space.
- Apply 2 light coats of frosted glass spray, 30 cm distance, sweeping passes.
- Wait 10 min between coats. Let cure 30 min before handling.

**Sand method:**
- Wet-sand the back face with 220-grit in circular motions.
- Rinse, dry, check diffusion by shining a phone flashlight through. Add more sanding if uneven.

### 2. Mask and Paint the Front Face
- Peel the protective film off the front face.
- Wipe with IPA.
- Lay on masking film and cut out mycelium strand shapes.
- Apply 2–3 coats of flat black paint with a sponge roller.
- Peel masking once fully dry. The strand areas should be completely clear acrylic.

### 3. Build the Light Box

Cut foam-core or MDF:
- **Back panel:** 30 × 20 cm
- **Side rails:** 2× at 30 × 4 cm (long sides)
- **End rails:** 2× at 20 × 4 cm (short sides)

Assemble with hot glue (foam-core) or wood glue + staples (MDF). The interior depth is 4 cm — enough air gap for light to spread.

Paint or line the interior with white. Even a sheet of white paper glued to the back panel works.

### 4. Mount LED Strips Inside the Box

Three rows of 30 cm strip, evenly spaced vertically (top, middle, bottom of the 20 cm height, so roughly at 3 cm, 10 cm, 17 cm from top).

- Stick strips to the white back panel with their self-adhesive backing.
- Wire them in series (DATA out of row 1 → DATA in of row 2 → row 3).
- Power (5 V / GND) can be tapped from the first strip's input pads and run to each row separately (parallel power, series data).

```
 Pico GP0 → [300Ω] → Row1 DIN
                       Row1 DOUT → Row2 DIN
                                    Row2 DOUT → Row3 DIN

 5V PSU ──────────→ Row1 5V   Row2 5V   Row3 5V  (parallel)
 GND   ──────────→ Row1 GND  Row2 GND  Row3 GND  (parallel)
```

Total LED count: 3 rows × 18 LEDs = 54 LEDs. Set `NUM_LEDS = 54` in firmware.

### 5. Wire the Pico

```
SK6812 Row 1          Pico
─────────────         ──────────────────
5 V   ────────────→  VBUS  (pin 40)  [only for < 300 mA; prefer external PSU]
GND   ──────────┬──→  GND   (pin 38)
DATA  →[300Ω]───┘──→  GP0   (pin 1)
470µF cap across 5V/GND at strip input
```

> Feed 5 V to all three strip rows from the PSU directly. Connect PSU GND to Pico GND. Do not power 54 LEDs through the Pico VBUS pin.

### 6. Attach the Acrylic

Mount the painted acrylic panel (frosted face toward interior) to the open face of the box:
- Use 4× M3 standoffs at corners so the acrylic is removable for adjustments.
- Or use hook-and-loop strips along all four edges for a tool-free swap.
- Seal any remaining gaps with black gaffer tape — any light leakage around the edges will wash out the strand effect.

### 7. Load Firmware

1. Flash Pico with MicroPython if not already done.
2. Copy `../firmware/panel_gradient.py` to the Pico as `main.py`.
3. Set `NUM_LEDS = 54`, `MODE = "A"` for first test.
4. Power up — strands should glow with a gradient running top-to-bottom.
5. Switch to `MODE = "B"` and re-run for the breathing effect.

---

## What to Observe

Stand 1–3 m back and note:

- **Banding** — can you see three distinct bright rows? (Increase air gap or add more frosting coats.)
- **Gradient evenness** — does the software gradient look smooth across the full panel?
- **Strand definition** — do edges of strands read crisply? (Too much frosting = softer edges.)
- **Brightness vs diffusion trade-off** — note how each extra coat of frost reduces peak strand brightness.
- **Mode A vs Mode B** at viewing distance.
- **Compare to Prototype 01** — which strand aesthetic reads better?

---

## Tuning Tips

| Problem | Fix |
|---|---|
| Visible strip banding | Increase air gap (deeper box) or add frosting coats |
| Strands look blurry | Reduce frosting (sand less / fewer spray coats) |
| Not bright enough | Increase `BRIGHTNESS` in firmware; check PSU amperage |
| Gradient looks stepped | Ensure `NUM_LEDS` matches actual count; try `GRADIENT_MIN = 0.1` |
| Paint adhesion poor on frosted face | Lightly wipe with IPA before painting (don't re-sand) |
| Light leaking around box edges | Gaffer tape all seams; check standoff gaps |

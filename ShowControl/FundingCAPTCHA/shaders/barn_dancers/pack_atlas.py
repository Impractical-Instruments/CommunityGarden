#!/usr/bin/env python3
"""Pack the barn puppet's layers into the Setup's one sprite sheet.

    pip install psd-tools            # only this script needs it
    python3 pack_atlas.py            # source/barn.psd → images/barn.png + common.glsl's ATLAS block

The "image" source binds one image per load (ADR-0024), so every part shares a
sheet. Its texture is linear-filtered with no mipmaps and straight from the
file, so the sheet is stored premultiplied by alpha (no dark fringes when
filtered or resized) and carries its own half- and quarter-size copies, which
the shader blends between as a barn gets smaller on screen.

The layers sit exploded on the PSD canvas. REST puts each one where it belongs
in the standing pose and JOINTS says where the legs hinge; both were measured
from the artist's reference dance cycle. Everything is in PSD pixels, y down.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE   = Path(__file__).parent
PSD    = HERE / "source" / "barn.psd"
SHEET  = HERE / "images" / "barn.png"
COMMON = HERE / "common.glsl"

# Draw order, back to front. Name → top-left corner in the standing pose.
REST = {
    "Eye L":    (645, 284),   "Eye R":    (954, 292),
    "Eyelid L": (670, 239),   "Eyelid R": (1045, 246),
    "Barn":     (473, 0),
    "Thigh L":  (355, 605),   "Foot L":   (368, 1022),  "Calf L":   (361, 798),
    "Thigh R":  (1096, 636),  "Foot R":   (1133, 1011), "Calf R":   (1166, 819),
}
JOINTS = {                    # left leg, right leg
    "HIP":   ((580, 677),  (1170, 710)),
    "KNEE":  ((410, 830),  (1352, 852)),
    "ANKLE": ((518, 1062), (1180, 1047)),
}
BARN_BOX = (473, 0, 1311, 752)        # the barn layer: its height is the rig's unit of length
GROUND_Y = 1163                       # the soles, standing
ORIGIN   = ((BARN_BOX[0] + BARN_BOX[2]) / 2, GROUND_Y)   # rig (0, 0): the ground under the barn's middle

SCALE = 0.5                           # PSD pixel → sheet texel at full size
PAD   = 8                             # clear texels around each part at full size
WIDTH = 640                           # full-size region; a multiple of 4
LODS  = 3                             # full, half and quarter size


def _layers() -> dict[str, Image.Image]:
    from psd_tools import PSDImage
    psd = PSDImage.open(PSD)
    found = {l.name: l for l in psd.descendants() if not l.is_group()}
    missing = [n for n in REST if n not in found]
    if missing:
        raise SystemExit(f"{PSD.name}: no layer named {', '.join(missing)}")
    return {n: found[n].topil().convert("RGBA") for n in REST}


def _clean(im: Image.Image) -> np.ndarray:
    """Premultiplied float RGBA with everything but the main shape erased (stray strokes)."""
    px = np.asarray(im, dtype=np.float32) / 255.0
    solid = px[..., 3] > 0.5
    labels, n = ndimage.label(solid)
    main = labels == 1 + int(np.argmax(ndimage.sum(solid, labels, range(1, n + 1))))
    keep = ndimage.binary_dilation(main, iterations=4)         # keeps the soft edge
    px[..., 3] *= keep
    px[..., :3] *= px[..., 3:4]
    return px


def _shrink(px: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    chans = [Image.fromarray(px[..., c], mode="F").resize(size, Image.Resampling.LANCZOS) for c in range(4)]
    return np.clip(np.stack([np.asarray(c) for c in chans], axis=-1), 0.0, 1.0)


def pack() -> None:
    parts = {}
    for name, im in _layers().items():
        px = _clean(im)
        ys, xs = np.nonzero(px[..., 3] > 0.01)
        x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1     # trim to what's left
        px = px[y0:y1, x0:x1]
        size = (max(1, round((x1 - x0) * SCALE)), max(1, round((y1 - y0) * SCALE)))
        parts[name] = (_shrink(px, size), (REST[name][0] + x0, REST[name][1] + y0, x1 - x0, y1 - y0))

    # Shelf-pack, tallest first.
    spots, x, y, shelf = {}, 0, 0, 0
    for name in sorted(parts, key=lambda n: -parts[n][0].shape[0]):
        h, w = parts[name][0].shape[:2]
        if x + w + 2 * PAD > WIDTH:
            x, y, shelf = 0, y + shelf, 0
        spots[name] = (x + PAD, y + PAD)
        x, shelf = x + w + 2 * PAD, max(shelf, h + 2 * PAD)
    height = -(-(y + shelf) // 4) * 4

    full = np.zeros((height, WIDTH, 4), dtype=np.float32)
    for name, (px, _) in parts.items():
        sx, sy = spots[name]
        full[sy:sy + px.shape[0], sx:sx + px.shape[1]] = px

    # Sheet: full size on the left, the smaller copies stacked to its right.
    sheet = np.zeros((height, WIDTH + WIDTH // 2, 4), dtype=np.float32)
    sheet[:, :WIDTH] = full
    lod_rects, top = [(0, 0, WIDTH, height)], 0
    for lod in range(1, LODS):
        w, h = WIDTH >> lod, height >> lod
        sheet[top:top + h, WIDTH:WIDTH + w] = _shrink(full, (w, h))
        lod_rects.append((WIDTH, top, w, h))
        top += h
    SHEET.parent.mkdir(exist_ok=True)
    Image.fromarray((sheet * 255.0 + 0.5).astype(np.uint8), mode="RGBA").save(SHEET, optimize=True)

    unit = float(BARN_BOX[3] - BARN_BOX[1])
    sw, sh = sheet.shape[1], sheet.shape[0]

    def rig(p):                               # PSD pixel → rig units, y up
        return ((p[0] - ORIGIN[0]) / unit, (ORIGIN[1] - p[1]) / unit)

    def v2(p):
        return f"vec2({p[0]:.4f}, {p[1]:.4f})"

    half = PAD / 2                            # each rectangle keeps this much clear border
    boxes, uvs = [], []
    for name in REST:
        px, (rx, ry, rw, rh) = parts[name]
        sx, sy = spots[name]
        ph, pw = px.shape[:2]
        m = half / SCALE
        lo, hi = rig((rx - m, ry + rh + m)), rig((rx + rw + m, ry - m))
        boxes.append(f"vec4({lo[0]:.4f}, {lo[1]:.4f}, {hi[0]:.4f}, {hi[1]:.4f})")
        # Fractions of the full-size region, v up (the player loads row 0 at the bottom).
        uvs.append(f"vec4({(sx - half) / WIDTH:.5f}, {1 - (sy + ph + half) / height:.5f}, "
                   f"{(sx + pw + half) / WIDTH:.5f}, {1 - (sy - half) / height:.5f})")
    lods = [f"vec4({x / sw:.5f}, {1 - (y + h) / sh:.5f}, {w / sw:.5f}, {h / sh:.5f})" for x, y, w, h in lod_rects]
    names = ", ".join(f"P_{n.upper().replace(' ', '_')} = {i}" for i, n in enumerate(REST))
    block = "\n".join([
        f"const int   PARTS = {len(REST)}, LODS = {LODS};",
        f"const int   {names};",
        "// Each part's rectangle in the standing pose (rig units: x0, y0, x1, y1) …",
        f"const vec4  PART_BOX[PARTS] = vec4[PARTS](\n    " + ",\n    ".join(boxes) + ");",
        "// … and in the full-size copy (fractions of it: u0, v0, u1, v1).",
        f"const vec4  PART_UV[PARTS] = vec4[PARTS](\n    " + ",\n    ".join(uvs) + ");",
        "// Where each copy sits in the sheet (UV origin, UV size): full, half, quarter.",
        f"const vec4  LOD_RECT[LODS] = vec4[LODS](" + ", ".join(lods) + ");",
        f"const float SHEET_UNIT = {unit * SCALE / sh:.5f};   // one rig unit at full size, as a fraction of the sheet's height",
        "// Leg joints, standing: [0] left leg, [1] right leg.",
        *(f"const vec2  {k}[2] = vec2[2]({v2(rig(a))}, {v2(rig(b))});" for k, (a, b) in JOINTS.items()),
        f"const float BODY_Y = {(GROUND_Y - BARN_BOX[3]) / unit:.4f};   // the barn's bottom edge above the ground, standing",
    ])
    text = COMMON.read_text()
    new, n = re.subn(r"(// ATLAS:BEGIN[^\n]*\n).*?(// ATLAS:END)", lambda m: m.group(1) + block + "\n" + m.group(2),
                     text, flags=re.S)
    if n != 1:
        raise SystemExit("common.glsl: no ATLAS:BEGIN … ATLAS:END block")
    COMMON.write_text(new)
    print(f"{SHEET.relative_to(HERE)}: {sw}×{sh}; ATLAS block in {COMMON.name} rewritten")


if __name__ == "__main__":
    pack()

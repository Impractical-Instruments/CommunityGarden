"""Aspect-preserving crop geometry for level images.

Level photos are arbitrary aspect ratios, but they are drawn into the
grid bounds, whose aspect is `cols/rows`. Scaling to fit distorts faces;
instead we crop the source to the destination aspect and scale that
uniformly. `crop_align` on the level chooses which part of the photo
survives the crop.
"""
from __future__ import annotations

# Fractional position of the kept region along each axis: 0.0 = flush with
# the top/left edge, 1.0 = flush with the bottom/right.
ANCHORS: dict[str, tuple[float, float]] = {
    "top-left":     (0.0, 0.0),
    "top":          (0.5, 0.0),
    "top-right":    (1.0, 0.0),
    "left":         (0.0, 0.5),
    "center":       (0.5, 0.5),
    "right":        (1.0, 0.5),
    "bottom-left":  (0.0, 1.0),
    "bottom":       (0.5, 1.0),
    "bottom-right": (1.0, 1.0),
}

DEFAULT_ALIGN = "center"


def crop_rect(src_w: int, src_h: int, dst_w: int, dst_h: int,
              align: object = DEFAULT_ALIGN) -> tuple[int, int, int, int]:
    """Largest sub-rect of the source matching the destination aspect.

    Returns (x, y, w, h). An unknown or malformed `align` falls back to
    center rather than raising — a hand-edited level file must never be
    able to take the show down mid-arc.
    """
    fx, fy = ANCHORS.get(align if isinstance(align, str) else "", ANCHORS[DEFAULT_ALIGN])

    if src_w * dst_h > src_h * dst_w:      # source is wider — trim the sides
        w = src_h * dst_w // dst_h
        h = src_h
    else:                                   # source is taller — trim top/bottom
        w = src_w
        h = src_w * dst_h // dst_w

    w = min(w, src_w)
    h = min(h, src_h)
    x = int((src_w - w) * fx)
    y = int((src_h - h) * fy)
    return x, y, w, h


def crop_scale(surface, dst_w: int, dst_h: int,
               align: object = DEFAULT_ALIGN):
    """Crop `surface` to the destination aspect, then scale it uniformly.

    `subsurface` is a view onto the original pixels, so the crop itself
    costs nothing; only the scale allocates.
    """
    import pygame

    rect = crop_rect(*surface.get_size(), dst_w, dst_h, align)
    return pygame.transform.scale(surface.subsurface(rect), (dst_w, dst_h))

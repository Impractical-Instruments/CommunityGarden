"""FundingCAPTCHA settings: where the files are, the default for every key, and how they merge.

    settings = load_settings()        # DEFAULTS ← captcha-settings.json ← captcha-settings.local.json

Every key the code reads has its default here, in DEFAULTS, and nowhere else:
readers index the result (`settings["camera"]["width"]`) with no fallback of
their own. A class that may be handed a partial dict (a test, a tool) calls
`with_defaults(settings)` first.

DEFAULTS equals the committed captcha-settings.json; test_settings.py holds the
two together. To change a default, change both.
"""
from __future__ import annotations

import json
import logging
from copy import deepcopy
from pathlib import Path

log = logging.getLogger("captcha.settings")

DIR            = Path(__file__).parent
SETTINGS       = DIR / "captcha-settings.json"
SETTINGS_LOCAL = DIR / "captcha-settings.local.json"     # per-host overrides; gitignored

DEFAULTS: dict = {
    "detection": {
        "depth_delta_mm":  30,
        "min_depth_mm":    1000,
        "max_depth_mm":    4000,
        "min_blob_pixels": 500,
    },
    "depth_slabs": [
        {"near_mm": 1000, "far_mm": 4000, "slab_id": 0},
    ],
    "slab_styles": {
        "0": {"color": [0, 220, 100]},
    },
    "cell_activation_threshold": 0.25,
    "camera_roi": {"x": 0, "y": 0, "w": 480, "h": 480},
    "silhouette_dilation_px": 1,
    "attract_dwell_s": 5.0,
    "min_foreground_pixels": 2000,
    "silhouette_opacity": 0.55,
    "background": {
        "warmup_s": 1.0,
        "min_valid_frames": 10,
        "reveal_frames": 5,
        "noise_k": 4,
        "bg_alpha": 0.01,
        "noise_alpha": 0.05,
        "absorb_s": 300,
        "reseed_fg_fraction": 0.4,
        "reseed_after_s": 30,
        "stats_log_s": 30,
    },
    "bodycaptcha": {
        "timer_s": 35,
        "hold_s": 1.0,
        "hold_decay_rate": 3.0,
        "hint_opacity": 0.2,
        "intensity_weights": {"difficulty": 0.4, "time_pressure": 0.6},
    },
    "shader_app": {
        "render_scale": 0.5,
        "display": 0,
        "fps": 30,
        "blobs": {
            "min_blob_pixels": 500,
            "min_confirm_frames": 4,
            "max_miss_frames": 8,
            "max_match_dist_px": 80,
            "smoothing_alpha": 0.5,
            "lost_hold_s": 1.0,
            "ease_s": 0.08,
        },
    },
    "camera": {
        "serial":  "",
        "width":   640,
        "height":  480,
        "fps":     15,
        "pos_cm":  [0, 0, 78],
        "rotation": {"pitch": -25, "yaw": 0, "roll": 0},
    },
}

# Blocks whose keys are data, not setting names: slab_styles is keyed by slab_id.
_OPEN_BLOCKS = {"slab_styles"}


def _merge(base: dict, over: dict) -> dict:
    """`over` on top of `base`. Blocks (dicts) merge key by key; anything else, lists included, is replaced whole."""
    out = deepcopy(base)
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = deepcopy(value)
    return out


def with_defaults(settings: dict) -> dict:
    """`settings` with every key it leaves out filled from DEFAULTS. Safe to call on an already complete dict."""
    return _merge(DEFAULTS, settings)


def unknown_keys(settings: dict, known: dict = DEFAULTS, prefix: str = "") -> list[str]:
    """Dotted paths of the keys in `settings` that DEFAULTS does not have: typos, or settings nothing reads.

    Keys starting with "_" are comments and are skipped.
    """
    found: list[str] = []
    for key, value in settings.items():
        if key.startswith("_"):
            continue
        path = f"{prefix}{key}"
        if key not in known:
            found.append(path)
        elif isinstance(value, dict) and isinstance(known[key], dict) and key not in _OPEN_BLOCKS:
            found.extend(unknown_keys(value, known[key], f"{path}."))
    return found


def _read(path: Path) -> dict:
    raw = json.loads(path.read_text())
    for key in unknown_keys(raw):
        log.warning("%s: unknown setting %r — nothing reads it (typo?)", path.name, key)
    return raw


def load_settings() -> dict:
    """DEFAULTS, then captcha-settings.json, then captcha-settings.local.json on top; warns on unknown keys.

    A local file that overrides part of a block keeps the rest of the block.
    A local file that does not parse is skipped with a warning.
    """
    merged: dict = {}
    if SETTINGS.exists():
        merged = _read(SETTINGS)
    if SETTINGS_LOCAL.exists():
        try:
            merged = _merge(merged, _read(SETTINGS_LOCAL))
        except Exception as exc:
            log.warning("%s unreadable, ignored: %s", SETTINGS_LOCAL.name, exc)
    return with_defaults(merged)


def slab_color(settings: dict, slab_id: int = 0) -> tuple[int, int, int]:
    """The silhouette colour of one depth slab, from slab_styles."""
    return tuple(settings["slab_styles"][str(slab_id)]["color"])

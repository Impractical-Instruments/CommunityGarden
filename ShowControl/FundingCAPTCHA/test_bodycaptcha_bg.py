"""A level's crop_align and image reach the photo loader (the cropping itself is tested in test_levels.py)."""
from __future__ import annotations

import games.bodycaptcha as bc


class RecordingLevels:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def background(self, name, w, h, align=None):
        self.calls.append((name, w, h, align))
        return None


def test_load_level_passes_crop_align_from_the_level(monkeypatch):
    """The level's crop_align must reach the loader — not be dropped in the middle."""
    levels = RecordingLevels()
    monkeypatch.setattr(bc, "_make_activator", lambda level, settings: None)
    game = bc.BodyCaptchaGame.__new__(bc.BodyCaptchaGame)
    game._settings = {}
    game._levels = levels
    game._WW, game._WH = 640, 480
    game._load_level({"image": "two_tone.png", "grid": [3, 3], "crop_align": "bottom"})
    name, _, _, align = levels.calls[0]
    assert (name, align) == ("two_tone.png", "bottom")

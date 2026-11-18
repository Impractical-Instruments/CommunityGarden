# FundingCAPTCHA games

One module per Game. `../plugins.py` (`load_games`) loads each by name and calls its `create(settings, size, levels)`: the settings, the screen's `(width, height)`, and the `Levels` (`../levels.py`) to play.

- **`bodycaptcha.py`** — BodyCaptcha, the only Game loaded today (ADR-0013, ADR-0019).
- **`grid.py`** — the shared grid overlay and Game-UI helpers (ADR-0019). Not a Game.

**Interface** (`Game` in `../arc.py`):

- `update(foreground, dt)` returns `(intensity 0–1, event)` where `event` is `'loss'`, `'win'` or `None`.
- `draw(surf)` renders one frame.
- `reset()` starts a fresh Arc.

Rules for a new Game:

- It must end in a loss on its own, with or without Players (see **Arc** in `CONTEXT.md`).
- Player input comes from the Body Grid (`../body_grid.py`), not from this directory.
- Level data lives beside `app.py` (`bodycaptcha-levels.json`, `taunts.json`), not here. Read levels and photos through the `Levels` you are given, never from a path of your own, and size yourself from `size`, not from the display.
- Add its name to `GAMES` in `../plugins.py`.
- Give its settings block in `captcha-settings.json` the same keys in `DEFAULTS` in `../settings.py`, and read them with no fallback of your own.

**Tests:** `../test_bodycaptcha_*.py`, `../test_plugins.py`.

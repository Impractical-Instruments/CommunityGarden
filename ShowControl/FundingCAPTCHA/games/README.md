# FundingCAPTCHA games

One module per Game. `app.py` (`_load_games`) loads each by name and calls its `create(settings)`.

- **`bodycaptcha.py`** — BodyCaptcha, the only Game loaded today (ADR-0013, ADR-0019).
- **`grid.py`** — the shared grid overlay and Game-UI helpers (ADR-0019). Not a Game.

**Interface** (`Game` in `../arc.py`):

- `update(foreground, dt)` returns `(intensity 0–1, event)` where `event` is `'loss'`, `'win'` or `None`.
- `draw(surf)` renders one frame.
- `reset()` starts a fresh Arc.

Rules for a new Game:

- It must end in a loss on its own, with or without Players (see **Arc** in `CONTEXT.md`).
- Player input comes from the Body Grid (`../body_grid.py`), not from this directory.
- Level data lives beside `app.py` (`bodycaptcha-levels.json`, `taunts.json`), not here.
- Add its name to the tuple in `app.py:_load_games`.

**Tests:** `../test_bodycaptcha_*.py`, `../test_app_games.py`.

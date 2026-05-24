"""
Club diorama rave screen — standalone pygame app (ADR-0017).

Rotates text messages from club_messages.txt on a 5" 800×480 HDMI LCD.
No OSC / GardenState integration; fully standalone.

Config keys (settings.json → club_screen):
  font_size_max         int   default 96
  font_size_min         int   default 36
  hold_top_seconds      float default 3
  scroll_speed_px_per_sec float default 60
  hold_bottom_seconds   float default 2
  fade_duration_seconds float default 0.5
  messages_file         str   default club_messages.txt
"""
import json
import logging
import os
import random
import sys
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "wayland")

import pygame

log = logging.getLogger("club_screen")

WIDTH, HEIGHT = 800, 480
FPS = 60
ACCENT = (0, 255, 200)
BG = (0, 0, 0)
SCANLINE_ALPHA = 40
SCANLINE_THICKNESS_PX = 4
PADDING_X = 40

_DIR = Path(__file__).parent

_FADE_IN = "fade_in"
_HOLD_TOP = "hold_top"
_SCROLL = "scroll"
_HOLD_BOTTOM = "hold_bottom"
_FADE_OUT = "fade_out"


def _load_config() -> dict:
    path = _DIR / "settings.json"
    if path.exists():
        with open(path) as f:
            return json.load(f).get("club_screen", {})
    return {}


def _load_messages(path: Path) -> list[str]:
    try:
        text = path.read_text()
        blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        return blocks or ["NO SIGNAL"]
    except Exception:
        log.warning("Could not read messages from %s", path)
        return ["NO SIGNAL"]


def _find_display(target: tuple[int, int]) -> int:
    sizes = pygame.display.get_desktop_sizes()
    for i, size in enumerate(sizes):
        if size == target:
            return i
    return 0


def _make_scanlines(width: int, height: int) -> pygame.Surface:
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(0, height, SCANLINE_THICKNESS_PX * 2):
        if y + SCANLINE_THICKNESS_PX >= height:
            break
        for yy in range(y, y + SCANLINE_THICKNESS_PX):
            pygame.draw.line(surf, (0, 0, 0, SCANLINE_ALPHA), (0, yy), (width - 1, yy))
    return surf


def _word_wrap(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split()
        current: list[str] = []
        for word in words:
            test = " ".join(current + [word])
            if font.size(test)[0] <= max_width:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))
    return lines


def _make_font(size: int) -> pygame.font.Font:
    return pygame.font.SysFont("monospace", size, bold=True)


def _fit_font(msg: str, size_max: int, size_min: int) -> tuple[pygame.font.Font, bool]:
    """Binary search for largest font where word-wrapped text fits HEIGHT. Falls back to min."""
    max_width = WIDTH - 2 * PADDING_X

    def fits(size: int) -> bool:
        f = _make_font(size)
        return f.get_linesize() * len(_word_wrap(f, msg, max_width)) <= HEIGHT

    if fits(size_max):
        return _make_font(size_max), True
    if not fits(size_min):
        return _make_font(size_min), False

    lo, hi = size_min, size_max
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if fits(mid):
            lo = mid
        else:
            hi = mid
    return _make_font(lo), True


def _build_message_surface(font: pygame.font.Font, msg: str, fits: bool) -> pygame.Surface:
    """Render full message to a surface. Vertically centered if it fits; top-aligned if scrolling."""
    max_width = WIDTH - 2 * PADDING_X
    lines = _word_wrap(font, msg, max_width)
    line_h = font.get_linesize()
    content_h = line_h * len(lines)
    surf_h = HEIGHT if fits else content_h
    surf = pygame.Surface((WIDTH, surf_h))
    surf.fill(BG)
    y = (HEIGHT - content_h) // 2 if fits else 0
    for line in lines:
        if line:
            rendered = font.render(line, True, ACCENT)
            x = (WIDTH - rendered.get_width()) // 2
            surf.blit(rendered, (x, y))
        y += line_h
    return surf


class _Deck:
    """Shuffle all items before repeating (no consecutive repeats across reshuffles)."""

    def __init__(self, items: list[str]) -> None:
        self.items = list(items)
        self._remaining: list[str] = []

    def next(self) -> str:
        if not self._remaining:
            self._remaining = list(self.items)
            random.shuffle(self._remaining)
        return self._remaining.pop()


class _MessageDisplay:
    def __init__(self, cfg: dict) -> None:
        self._size_max = int(cfg.get("font_size_max", 96))
        self._size_min = int(cfg.get("font_size_min", 36))
        self._hold_top = float(cfg.get("hold_top_seconds", 3))
        self._scroll_speed = float(cfg.get("scroll_speed_px_per_sec", 60))
        self._hold_bottom = float(cfg.get("hold_bottom_seconds", 2))
        self._fade_dur = float(cfg.get("fade_duration_seconds", 0.5))

        self._surf: pygame.Surface | None = None
        self._fits = True
        self._state = _FADE_IN
        self._state_t = time.monotonic()
        self._scroll_y = 0.0
        self._alpha = 0

    def load(self, msg: str) -> None:
        font, fits = _fit_font(msg, self._size_max, self._size_min)
        self._surf = _build_message_surface(font, msg, fits)
        self._fits = fits
        self._scroll_y = 0.0
        self._state = _FADE_IN
        self._state_t = time.monotonic()
        self._alpha = 0

    def update(self, dt: float) -> bool:
        """Returns True when this message is finished and the next should load."""
        now = time.monotonic()
        elapsed = now - self._state_t

        if self._state == _FADE_IN:
            self._alpha = min(255, int(255 * elapsed / max(self._fade_dur, 0.001)))
            if elapsed >= self._fade_dur:
                self._alpha = 255
                self._state = _HOLD_TOP
                self._state_t = now

        elif self._state == _HOLD_TOP:
            if elapsed >= self._hold_top:
                self._state = _SCROLL if not self._fits else _HOLD_BOTTOM
                self._state_t = now

        elif self._state == _SCROLL:
            assert self._surf is not None
            max_scroll = self._surf.get_height() - HEIGHT
            self._scroll_y = min(float(max_scroll), self._scroll_y + self._scroll_speed * dt)
            if self._scroll_y >= max_scroll:
                self._state = _HOLD_BOTTOM
                self._state_t = now

        elif self._state == _HOLD_BOTTOM:
            if elapsed >= self._hold_bottom:
                self._state = _FADE_OUT
                self._state_t = now

        elif self._state == _FADE_OUT:
            self._alpha = max(0, int(255 * (1.0 - elapsed / max(self._fade_dur, 0.001))))
            if elapsed >= self._fade_dur:
                return True

        return False

    def render(self, screen: pygame.Surface, scanlines: pygame.Surface) -> None:
        screen.fill(BG)
        if self._surf is not None:
            src_y = int(self._scroll_y)
            clip = pygame.Rect(0, src_y, WIDTH, HEIGHT)
            frame = self._surf.subsurface(clip).copy()
            frame.set_alpha(self._alpha)
            screen.blit(frame, (0, 0))
        screen.blit(scanlines, (0, 0))
        pygame.display.flip()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    cfg = _load_config()
    _default_msgs = str(_DIR / "club_messages.txt")
    messages_file = Path(cfg.get("messages_file", _default_msgs))
    if not messages_file.is_absolute():
        messages_file = _DIR / messages_file

    pygame.init()
    display_index = _find_display((WIDTH, HEIGHT))
    log.info("Club screen on display %d", display_index)
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN, display=display_index)
    pygame.display.set_caption("Club Screen")
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()

    scanlines = _make_scanlines(WIDTH, HEIGHT)
    messages = _load_messages(messages_file)
    deck = _Deck(messages)
    display = _MessageDisplay(cfg)
    display.load(deck.next())

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit(0)

        if display.update(dt):
            messages = _load_messages(messages_file)
            deck.items = messages
            display.load(deck.next())

        display.render(screen, scanlines)


if __name__ == "__main__":
    main()

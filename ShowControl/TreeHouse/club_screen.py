"""
Club diorama rave screen — standalone pygame app (ADR-0017).

Rotates text messages from club_messages.txt on a 5" 800×480 HDMI LCD.
No OSC / GardenState integration; fully standalone.
"""
import json
import logging
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "wayland")

import pygame

log = logging.getLogger("club_screen")

WIDTH, HEIGHT = 800, 480
FPS = 30
ACCENT = (0, 255, 200)
BG = (0, 0, 0)
SCANLINE_ALPHA = 40
FONT_SIZE = 96

_DIR = Path(__file__).parent


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
    for y in range(0, height, 2):
        pygame.draw.line(surf, (0, 0, 0, SCANLINE_ALPHA), (0, y), (width - 1, y))
    return surf


def _render(screen: pygame.Surface, font: pygame.font.Font, msg: str, scanlines: pygame.Surface) -> None:
    screen.fill(BG)
    lines = msg.splitlines()
    line_h = font.get_linesize()
    total_h = line_h * len(lines)
    y = (HEIGHT - total_h) // 2
    for line in lines:
        surf = font.render(line, True, ACCENT)
        x = (WIDTH - surf.get_width()) // 2
        screen.blit(surf, (x, y))
        y += line_h
    screen.blit(scanlines, (0, 0))
    pygame.display.flip()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    cfg = _load_config()
    interval: float = float(cfg.get("interval_seconds", 10))
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

    font = pygame.font.SysFont("monospace", FONT_SIZE, bold=True)
    scanlines = _make_scanlines(WIDTH, HEIGHT)

    messages = _load_messages(messages_file)
    idx = 0
    last_rotate = time.monotonic()
    _render(screen, font, messages[idx], scanlines)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit(0)

        if time.monotonic() - last_rotate >= interval:
            messages = _load_messages(messages_file)
            idx = (idx + 1) % max(len(messages), 1)
            _render(screen, font, messages[idx], scanlines)
            last_rotate = time.monotonic()

        clock.tick(FPS)


if __name__ == "__main__":
    main()

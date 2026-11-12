"""Playlist player — shader Setups and full-screen videos, shuffled together.

playlist.json lists Setups (shaders/<name>/) and videos (videos/<file>,
gitignored: copy them onto the show PC). One shuffle bag holds both, so
every item plays once before any repeats; setup_copies puts each Setup in
the bag that many times, so videos come round less often. A Setup plays for
the playlist's setup_duration_s (overriding its own duration_s); a video plays to the end
of its file, silent and letterboxed. Between every two items an optional
interstitial Setup (the logo) plays for interstitial_s.

The camera runs throughout, so the depth background keeps learning (ADR-0023)
and Setups find the Body live whenever they come round.

  python3 playlist_app.py --camera                 # show
  python3 playlist_app.py --mock-camera --windowed # drifting fake bodies
  python3 playlist_app.py --test-input --windowed  # mouse paints the Body

Keys: N / → next item · R reload current Setup from disk · Esc quit.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from app import DIR, load_settings
from arc import ShuffleBag
from shader_app import (SHADER_DIR, SetupImages, ShaderStage, add_mode_args, display_index,
                        drain_camera, open_display, start_camera)
from shadertoy import Renderer, load_setup

log = logging.getLogger("playlist_app")

PLAYLIST_PATH = DIR / "playlist.json"
VIDEO_DIR     = DIR / "videos"
RETRY_S       = 5.0         # nothing would play: try the bag again after this
QUEUE_FRAMES  = 8           # decoded frames buffered ahead of the screen


# ── Playlist file ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Item:
    kind: str               # "setup" | "video"
    name: str               # Setup folder name, or video path (relative to videos/)

    def __str__(self) -> str:
        return f"{self.kind} {self.name}"


@dataclass
class PlaylistConfig:
    items:            list[Item]
    setup_duration_s: float
    interstitial:     Item | None = None    # a Setup played between every two items
    interstitial_s:   float = 30.0


def load_playlist(path: Path) -> PlaylistConfig:
    cfg = json.loads(Path(path).read_text())
    copies = max(1, int(cfg.get("setup_copies", 1)))
    items = ([Item("setup", n) for n in cfg.get("setups", []) for _ in range(copies)]
             + [Item("video", n) for n in cfg.get("videos", [])])
    between = cfg.get("interstitial")
    return PlaylistConfig(items, float(cfg.get("setup_duration_s", 300.0)),
                          Item("setup", between) if between else None,
                          float(cfg.get("interstitial_s", 30.0)))


# ── Video ─────────────────────────────────────────────────────────────────────

class VideoPlayer:
    """Decodes one file on a thread; frame() hands out the frame due now.

    Time starts at the first decoded frame, so opening the file doesn't eat
    into the picture. If decoding falls behind, every frame is still shown —
    the video runs long rather than skipping. A file tagged as rotated (a
    phone held upright) is turned to match, as any player shows it.
    """

    def __init__(self, path: Path, clock: Callable[[], float] = time.monotonic) -> None:
        import av
        self.path   = Path(path)
        self._clock = clock
        self._container = av.open(str(path))
        try:
            self._stream = self._container.streams.video[0]
        except IndexError:
            self._container.close()
            raise ValueError(f"{self.path.name}: no video stream") from None
        self._stream.thread_type = "AUTO"
        self.rate  = float(self._stream.average_rate or 30)
        self.error: Exception | None = None
        self._q    = queue.Queue(maxsize=QUEUE_FRAMES)
        self._stop = threading.Event()
        self._eof  = threading.Event()
        self._pending = None                      # (t, rgb) decoded but not yet due
        self._t0 = self._pts0 = None
        self._end_at: float | None = None         # clock time the last frame shown expires
        self._thread = threading.Thread(target=self._decode, daemon=True,
                                        name=f"video {self.path.name}")
        self._thread.start()

    def _decode(self) -> None:
        try:
            for n, frame in enumerate(self._container.decode(self._stream)):
                if self._stop.is_set():
                    return
                t = frame.time if frame.time is not None else n / self.rate
                rgb = frame.to_ndarray(format="rgb24")
                turns = quarter_turns(self._stream, frame)
                if turns:
                    rgb = np.rot90(rgb, turns)
                item = (t, rgb)
                while not self._stop.is_set():
                    try:
                        self._q.put(item, timeout=0.1)
                        break
                    except queue.Full:
                        continue
        except Exception as exc:                  # a corrupt file ends the video, not the show
            self.error = exc
        finally:
            self._eof.set()

    def frame(self) -> np.ndarray | None:
        """The newest frame now due (row 0 = top, RGB8), or None if nothing new."""
        now, latest = self._clock(), None
        while True:
            if self._pending is None:
                try:
                    self._pending = self._q.get_nowait()
                except queue.Empty:
                    break
            t, rgb = self._pending
            if self._t0 is None:
                self._t0, self._pts0 = now, t
            if t - self._pts0 > now - self._t0:
                break
            latest, self._pending = rgb, None
            self._end_at = max(now, self._t0 + t - self._pts0) + 1.0 / self.rate
        return latest

    @property
    def done(self) -> bool:
        return (self._eof.is_set() and self._pending is None and self._q.empty()
                and (self._end_at is None or self._clock() >= self._end_at))

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2.0)
        if self._thread.is_alive():
            log.warning("%s: decoder didn't stop; leaving the file open", self.path.name)
            return
        self._container.close()


def quarter_turns(stream, frame) -> int:
    """Counter-clockwise quarter turns the file's display matrix asks for.

    Older PyAV reports the angle on the stream, newer on each frame.
    """
    angle = getattr(frame, "rotation", None)
    if angle is None:
        angle = (getattr(stream, "side_data", None) or {}).get("DISPLAYMATRIX", 0)
    return round(float(angle or 0) / 90) % 4


def fit_rect(src: tuple[int, int], dst: tuple[int, int]) -> tuple[int, int, int, int]:
    """Largest src-aspect rect centred in dst → (x, y, w, h). Letterbox or pillarbox."""
    scale = min(dst[0] / src[0], dst[1] / src[1])
    w, h  = max(1, round(src[0] * scale)), max(1, round(src[1] * scale))
    return (dst[0] - w) // 2, (dst[1] - h) // 2, w, h


_VIDEO_VERT = """
#version 330
in vec2 in_vert;
out vec2 uv;
void main() {
    uv = vec2(in_vert.x * 0.5 + 0.5, 0.5 - in_vert.y * 0.5);   // texture row 0 = top of picture
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
"""

_VIDEO_FRAG = """
#version 330
uniform sampler2D src;
in vec2 uv;
out vec4 c;
void main() { c = vec4(texture(src, uv).rgb, 1.0); }
"""


class VideoScreen:
    """The latest video frame, letterboxed on black."""

    def __init__(self, ctx, win: tuple[int, int], vbo) -> None:
        import moderngl
        self._mgl = moderngl
        self.ctx, self.win = ctx, win
        self._prog = ctx.program(vertex_shader=_VIDEO_VERT, fragment_shader=_VIDEO_FRAG)
        self._vao  = ctx.vertex_array(self._prog, [(vbo, "2f", "in_vert")])
        self._tex  = None

    def show(self, rgb: np.ndarray) -> None:
        size = (rgb.shape[1], rgb.shape[0])
        if self._tex is None or self._tex.size != size:
            self.clear()
            self._tex = self.ctx.texture(size, 3, alignment=1)
            self._tex.filter = (self._mgl.LINEAR, self._mgl.LINEAR)
            self._tex.repeat_x = self._tex.repeat_y = False
        self._tex.write(np.ascontiguousarray(rgb))

    def draw(self) -> None:
        self.ctx.screen.use()
        self.ctx.viewport = (0, 0, *self.win)
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        if self._tex is None:
            return
        self.ctx.viewport = fit_rect(self._tex.size, self.win)
        self._tex.use(location=0)
        self._prog["src"].value = 0
        self._vao.render(self._mgl.TRIANGLE_STRIP)

    def clear(self) -> None:
        """Forget the last frame, so the next video doesn't open on it."""
        if self._tex is not None:
            self._tex.release()
            self._tex = None

    def release(self) -> None:
        self.clear()
        self._vao.release()
        self._prog.release()


# ── Rotation ──────────────────────────────────────────────────────────────────

class Playlist:
    """Which item plays: one shuffle bag of Setups and videos.

    With an `interstitial` Setup, it plays for `interstitial_s` after every
    item, before the next is drawn from the bag. If it won't load, the bag
    carries straight on; if it fails at render time, it's dropped for the run.

    An item that won't load is skipped for this draw. A Setup that fails at
    render time is dropped for the rest of the run (as shader_app.Rotation).
    """

    def __init__(self, renderer: Renderer, items: list[Item], setup_duration_s: float,
                 shader_dir: Path = SHADER_DIR, video_dir: Path = VIDEO_DIR,
                 open_video: Callable[[Path], VideoPlayer] = VideoPlayer,
                 clock: Callable[[], float] = time.monotonic,
                 on_load: Callable[[], None] | None = None,
                 interstitial: Item | None = None, interstitial_s: float = 30.0,
                 image_max: tuple[int, int] = (4096, 4096), image_max_side: int = 16384) -> None:
        self.renderer   = renderer
        self._images    = SetupImages(image_max, image_max_side)
        self.items      = list(items)
        self.setup_duration_s = setup_duration_s
        self._bag       = ShuffleBag(self.items)
        self._shaders   = shader_dir
        self._videos    = video_dir
        self._open_video = open_video
        self._clock     = clock
        self._on_load   = on_load                 # after every Setup load
        self.interstitial   = interstitial
        self.interstitial_s = interstitial_s
        self.in_interstitial = False              # the current item is the interstitial
        self.current: Item | None = None
        self.video:   VideoPlayer | None = None
        self.started  = clock()

    def next(self) -> None:
        """End the current item: the interstitial after an item, a bag item after that."""
        if (self.interstitial is not None and self.current is not None
                and not self.in_interstitial and self._start_interstitial()):
            return
        if (self.interstitial is None and len(self.items) == 1 and self.current is not None
                and self.current.kind == "setup" and self.renderer.setup is not None):
            self.started = self._clock()          # nothing else to play; keep its state
            return
        for _ in range(max(1, len(self.items))):
            item = self._bag.next()
            if item is None:
                break
            if self._start(item):
                return
        log.error("Nothing in the playlist would start — retrying in %.0fs", RETRY_S)
        self._stop_video()
        if self.current is not None and self.current.kind == "video":
            self.current = None
        self.started = self._clock()

    def tick(self) -> None:
        elapsed = self._clock() - self.started
        if self.current is None:
            if elapsed >= RETRY_S:
                self.next()
        elif self.in_interstitial:
            if elapsed >= self.interstitial_s:
                self.next()
        elif self.current.kind == "setup":
            if elapsed >= self.setup_duration_s:
                self.next()
        elif self.video is not None and self.video.done:
            if self.video.error is not None:
                log.error("Video %s stopped early: %s", self.current.name, self.video.error)
            self.next()

    def reload(self) -> None:
        """Re-read the current Setup from disk; a broken edit keeps the old one."""
        if self.current is not None and self.current.kind == "setup":
            self._load_setup(self.current.name)

    def failed(self, exc: Exception) -> None:
        item = self.current
        log.error("%s failed while rendering, dropped: %s", item, exc)
        self.renderer.unload()
        self.current = None
        if self.in_interstitial:
            self.interstitial, self.in_interstitial = None, False
        elif item in self.items:
            self.items = [i for i in self.items if i != item]   # every copy
            self._bag = ShuffleBag(self.items)
        self.next()

    def close(self) -> None:
        self._stop_video()

    @property
    def playing_video(self) -> bool:
        return self.video is not None

    def _start(self, item: Item) -> bool:
        if item.kind == "setup":
            if not self._load_setup(item.name):
                return False
            self._stop_video()
        else:
            try:
                video = self._open_video(self._videos / item.name)
            except Exception as exc:              # missing / unreadable file: never fatal
                log.error("Video %s skipped: %s", item.name, exc)
                return False
            self._stop_video()
            self.renderer.unload()                # free the Setup's buffers while the video plays
            self.video = video
        self.current, self.in_interstitial = item, False
        self.started = self._clock()
        log.info("Playing %s", item)
        return True

    def _start_interstitial(self) -> bool:
        if not self._load_setup(self.interstitial.name):
            return False
        self._stop_video()
        self.current, self.in_interstitial = self.interstitial, True
        self.started = self._clock()
        log.info("Playing %s (interstitial)", self.current)
        return True

    def _load_setup(self, name: str) -> bool:
        try:
            setup = load_setup(self._shaders / name)
            image = self._images.next(setup) if setup.uses_image else None
            self.renderer.load(setup, image=image)
        except Exception as exc:                  # team-authored content: never fatal
            log.error("Setup %s skipped: %s", name, exc)
            return False
        if self._on_load is not None:
            self._on_load()
        return True

    def _stop_video(self) -> None:
        if self.video is not None:
            self.video.close()
            self.video = None


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="Shader Setups and full-screen videos, shuffled")
    add_mode_args(ap)
    ap.add_argument("--playlist", type=Path, default=PLAYLIST_PATH,
                    help="Playlist file (default: playlist.json)")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    settings = load_settings()
    fps      = int(settings.get("shader_app", {}).get("fps", 30))
    playlist_cfg = load_playlist(args.playlist)
    for item in playlist_cfg.items:
        if item.kind == "video" and not (VIDEO_DIR / item.name).is_file():
            log.warning("Video %s not found in %s — it will be skipped", item.name, VIDEO_DIR)

    ctx, win = open_display(args.windowed, "Playlist player", args.test_input,
                            display_index(args, settings))
    stage    = ShaderStage(ctx, win, settings, args.test_input)
    screen   = VideoScreen(ctx, win, stage.renderer.vbo)
    playlist = Playlist(stage.renderer, playlist_cfg.items, playlist_cfg.setup_duration_s,
                        on_load=stage.blobs.reset,
                        interstitial=playlist_cfg.interstitial,
                        interstitial_s=playlist_cfg.interstitial_s,
                        image_max=win, image_max_side=stage.max_texture_side)
    playlist.next()
    cam_q, stop = start_camera(args, settings)

    import pygame
    clock     = pygame.time.Clock()
    fps_t, fps_n = time.monotonic(), 0
    running   = True
    showing   = None
    while running:
        # A video gets a loop at least as fast as its own frame rate.
        rate = max(fps, math.ceil(playlist.video.rate)) if playlist.playing_video else fps
        dt   = min(clock.tick(rate) / 1000.0, 0.25)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key in (pygame.K_n, pygame.K_RIGHT):
                    playlist.next()
                elif ev.key == pygame.K_r:
                    playlist.reload()
                stage.handle_key(ev)
            elif ev.type == pygame.KEYUP:
                stage.handle_key(ev)

        playlist.tick()
        fg = drain_camera(cam_q)                  # always drain: the camera thread blocks when full

        if playlist.video is not showing:
            screen.clear()
            showing = playlist.video
        if playlist.playing_video:
            rgb = playlist.video.frame()
            if rgb is not None:
                screen.show(rgb)
            screen.draw()
        elif stage.renderer.setup is not None:
            failure = stage.frame(dt, fg)
            if failure is not None:
                playlist.failed(failure)
        else:
            screen.draw()                         # nothing playable: black
        pygame.display.flip()

        fps_n += 1
        if time.monotonic() - fps_t >= 10.0:
            log.info("%.1f fps · %s", fps_n / (time.monotonic() - fps_t),
                     playlist.current or "-")
            fps_t, fps_n = time.monotonic(), 0

    stop.set()
    playlist.close()
    screen.release()
    stage.release()
    pygame.quit()


if __name__ == "__main__":
    main()

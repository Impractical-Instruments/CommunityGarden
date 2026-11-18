"""Video playback for the kiosk screen: decode a file on a thread, hand out the frame due, letterbox it."""
from __future__ import annotations

import logging
import queue
import threading
import time
from pathlib import Path
from typing import Callable

import numpy as np

log = logging.getLogger("video_player")

QUEUE_FRAMES = 8            # decoded frames buffered ahead of the screen


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

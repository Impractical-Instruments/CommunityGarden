"""playlist_app.py: playlist file, video decoding and pacing, letterbox, rotation."""
import json
import time
from pathlib import Path

import numpy as np
import pytest

from playlist_app import (Item, Playlist, VideoPlayer, fit_rect, load_playlist,
                          quarter_turns)
from shadertoy import Renderer
from test_shadertoy import SOLID, _image_setup, _rendered_colour


# ── Playlist file ─────────────────────────────────────────────────────────────

def test_load_playlist(tmp_path):
    p = tmp_path / "playlist.json"
    p.write_text(json.dumps({"setup_duration_s": 300, "setups": ["a"], "videos": ["v.mp4"]}))
    cfg = load_playlist(p)
    assert cfg.items == [Item("setup", "a"), Item("video", "v.mp4")]
    assert cfg.setup_duration_s == 300


def test_load_playlist_setup_copies(tmp_path):
    p = tmp_path / "playlist.json"
    p.write_text(json.dumps({"setup_duration_s": 300, "setup_copies": 2,
                             "setups": ["a", "b"], "videos": ["v.mp4"]}))
    assert load_playlist(p).items == [Item("setup", "a"), Item("setup", "a"),
                                      Item("setup", "b"), Item("setup", "b"),
                                      Item("video", "v.mp4")]


def test_shipped_playlist_names_real_setups():
    cfg = load_playlist(Path(__file__).parent / "playlist.json")
    shaders = Path(__file__).parent / "shaders"
    for item in cfg.items:
        if item.kind == "setup":
            assert (shaders / item.name / "image.glsl").exists(), item.name


# ── Letterbox ─────────────────────────────────────────────────────────────────

def test_fit_rect_letterboxes_wide_video():
    assert fit_rect((1920, 800), (1920, 1080)) == (0, 140, 1920, 800)


def test_fit_rect_pillarboxes_tall_video():
    assert fit_rect((1080, 1080), (1920, 1080)) == (420, 0, 1080, 1080)


def test_fit_rect_scales_up():
    assert fit_rect((640, 360), (1920, 1080)) == (0, 0, 1920, 1080)


# ── Video ─────────────────────────────────────────────────────────────────────

def _write_video(path: Path, n: int = 6, rate: int = 10) -> Path:
    av = pytest.importorskip("av")
    with av.open(str(path), "w") as out:
        s = out.add_stream("mpeg4", rate=rate)
        s.width, s.height, s.pix_fmt = 32, 16, "yuv420p"
        for i in range(n):
            img = np.zeros((16, 32, 3), dtype=np.uint8)
            img[..., 0] = i * 40                  # red encodes the frame number
            for pkt in s.encode(av.VideoFrame.from_ndarray(img, format="rgb24")):
                out.mux(pkt)
        for pkt in s.encode():
            out.mux(pkt)
    return path


def _wait(cond, timeout=5.0):
    end = time.monotonic() + timeout
    while not cond():
        assert time.monotonic() < end, "timed out"
        time.sleep(0.01)


def test_video_paces_frames_and_ends(tmp_path):
    now = [100.0]
    v = VideoPlayer(_write_video(tmp_path / "v.mp4"), clock=lambda: now[0])
    try:
        assert v.rate == 10
        _wait(lambda: not v._q.empty())
        first = v.frame()
        assert first is not None and first.shape == (16, 32, 3)
        assert v.frame() is None                  # next frame not due yet
        now[0] += 0.25
        _wait(lambda: v._eof.is_set())
        mid = v.frame()
        assert mid is not None and mid[..., 0].mean() == pytest.approx(80, abs=12)   # frame 2
        assert not v.done
        now[0] += 0.3                             # last frame (t=0.5) due
        assert v.frame() is not None
        assert not v.done                         # it still gets its 1/rate on screen
        now[0] += 0.1
        assert v.done and v.error is None
    finally:
        v.close()


class _Tagged:
    def __init__(self, **attrs):
        self.__dict__.update(attrs)


@pytest.mark.parametrize("stream, frame, turns", [
    (_Tagged(side_data={"DISPLAYMATRIX": 90.0}), _Tagged(), 1),      # older PyAV: on the stream
    (_Tagged(), _Tagged(rotation=90), 1),                            # newer PyAV: on the frame
    (_Tagged(), _Tagged(rotation=-90), 3),
    (_Tagged(side_data={}), _Tagged(), 0),
    (_Tagged(), _Tagged(rotation=0), 0),
])
def test_quarter_turns_reads_the_display_matrix(stream, frame, turns):
    assert quarter_turns(stream, frame) == turns


def test_missing_video_raises(tmp_path):
    pytest.importorskip("av")
    with pytest.raises(Exception):
        VideoPlayer(tmp_path / "nope.mp4")


# ── Playlist rotation ─────────────────────────────────────────────────────────

class _FakeVideo:
    rate = 30.0

    def __init__(self, path):
        if not Path(path).name.startswith("ok"):
            raise FileNotFoundError(path)
        self.path, self.done, self.error, self.closed = Path(path), False, None, False

    def close(self):
        self.closed = True


def _setups(root: Path, *names: str) -> Path:
    for name in names:
        (root / name).mkdir()
        (root / name / "image.glsl").write_text(SOLID)
        (root / name / "setup.json").write_text(json.dumps({"duration_s": 10}))
    return root


def _playlist(ctx, tmp_path, items, now):
    r = Renderer(ctx, (4, 4))
    pl = Playlist(r, items, 300, shader_dir=_setups(tmp_path, "a", "b"),
                  video_dir=tmp_path, open_video=_FakeVideo, clock=lambda: now[0])
    return r, pl


def test_setup_plays_playlist_duration_not_its_own(ctx, tmp_path):
    now = [0.0]
    r, pl = _playlist(ctx, tmp_path, [Item("setup", "a"), Item("setup", "b")], now)
    pl.next()
    first = pl.current
    now[0] = 11.0                                 # past the Setup's own duration_s
    pl.tick()
    assert pl.current == first
    now[0] = 300.0
    pl.tick()
    assert pl.current != first
    r.release()


def test_video_plays_until_done_then_closes(ctx, tmp_path):
    now = [0.0]
    r, pl = _playlist(ctx, tmp_path, [Item("video", "ok.mp4"), Item("setup", "a")], now)
    pl._bag.next = iter([Item("video", "ok.mp4"), Item("setup", "a")]).__next__
    pl.next()
    video = pl.video
    assert pl.playing_video and r.setup is None
    now[0] = 1000.0
    pl.tick()
    assert pl.video is video                      # no time limit on videos
    video.done = True
    pl.tick()
    assert video.closed and pl.video is None and pl.current == Item("setup", "a")
    assert r.setup is not None and r.setup.name == "a"
    r.release()


def test_missing_video_is_skipped(ctx, tmp_path):
    now = [0.0]
    r, pl = _playlist(ctx, tmp_path, [Item("video", "gone.mp4"), Item("setup", "a")], now)
    pl._bag.next = iter([Item("video", "gone.mp4"), Item("setup", "a")]).__next__
    pl.next()
    assert pl.current == Item("setup", "a") and not pl.playing_video
    r.release()


def test_nothing_playable_goes_black_then_retries(ctx, tmp_path):
    now = [0.0]
    r, pl = _playlist(ctx, tmp_path, [Item("video", "gone.mp4")], now)
    pl.next()
    assert pl.current is None
    calls = []
    pl.next = lambda: calls.append(now[0])
    now[0] = 1.0
    pl.tick()
    assert calls == []
    now[0] = 5.0
    pl.tick()
    assert calls == [5.0]
    r.release()


def test_render_failure_drops_setup(ctx, tmp_path):
    now = [0.0]
    r, pl = _playlist(ctx, tmp_path, [Item("setup", "a"), Item("video", "ok.mp4")], now)
    pl._bag.next = iter([Item("setup", "a")]).__next__
    pl.next()
    pl.failed(RuntimeError("boom"))
    assert pl.items == [Item("video", "ok.mp4")]
    assert pl.playing_video
    r.release()


def test_render_failure_drops_every_copy_of_setup(ctx, tmp_path):
    now = [0.0]
    r, pl = _playlist(ctx, tmp_path, [Item("setup", "a"), Item("setup", "a"),
                                      Item("video", "ok.mp4")], now)
    pl._bag.next = iter([Item("setup", "a")]).__next__
    pl.next()
    pl.failed(RuntimeError("boom"))
    assert pl.items == [Item("video", "ok.mp4")]
    r.release()


def test_single_setup_is_not_reloaded_on_expiry(ctx, tmp_path):
    now = [0.0]
    r, pl = _playlist(ctx, tmp_path, [Item("setup", "a")], now)
    pl.next()
    first = r.setup
    now[0] = 300.0
    pl.tick()
    assert r.setup is first and pl.started == 300.0
    r.release()


def test_setup_gets_a_shuffled_image_per_load(ctx, tmp_path):
    """The "image" source works under the playlist as under shader_app.Rotation (ADR-0024)."""
    _image_setup(tmp_path, {"r.png": (255, 0, 0, 255), "g.png": (0, 255, 0, 255)})
    r = Renderer(ctx, (4, 4))
    pl = Playlist(r, [Item("setup", "s")], 300, shader_dir=tmp_path, video_dir=tmp_path)
    pl.next()
    seen = [_rendered_colour(r)]
    pl.reload()
    seen.append(_rendered_colour(r))
    assert set(seen) == {(255, 0, 0, 255), (0, 255, 0, 255)}
    r.release()


# ── Interstitial ──────────────────────────────────────────────────────────────

def test_load_playlist_interstitial(tmp_path):
    p = tmp_path / "playlist.json"
    p.write_text(json.dumps({"setups": ["a"], "interstitial": "logo", "interstitial_s": 12}))
    cfg = load_playlist(p)
    assert cfg.interstitial == Item("setup", "logo") and cfg.interstitial_s == 12
    p.write_text(json.dumps({"setups": ["a"]}))
    assert load_playlist(p).interstitial is None


def test_shipped_interstitial_is_a_real_setup():
    cfg = load_playlist(Path(__file__).parent / "playlist.json")
    assert cfg.interstitial is not None
    assert (Path(__file__).parent / "shaders" / cfg.interstitial.name / "image.glsl").exists()


def _between(ctx, tmp_path, items, now, interstitial="i"):
    r = Renderer(ctx, (4, 4))
    pl = Playlist(r, items, 300, shader_dir=_setups(tmp_path, "a", "b", "i"),
                  video_dir=tmp_path, open_video=_FakeVideo, clock=lambda: now[0],
                  interstitial=Item("setup", interstitial), interstitial_s=30)
    return r, pl


def test_interstitial_plays_between_items(ctx, tmp_path):
    now = [0.0]
    r, pl = _between(ctx, tmp_path, [Item("setup", "a"), Item("video", "ok.mp4")], now)
    pl._bag.next = iter([Item("setup", "a"), Item("video", "ok.mp4"), Item("setup", "a")]).__next__
    pl.next()
    assert pl.current == Item("setup", "a") and not pl.in_interstitial   # the show opens on an item
    now[0] = 300.0
    pl.tick()
    assert pl.in_interstitial and r.setup.name == "i"
    now[0] = 329.0
    pl.tick()
    assert pl.in_interstitial
    now[0] = 330.0
    pl.tick()
    assert pl.current == Item("video", "ok.mp4") and not pl.in_interstitial
    video = pl.video
    video.done = True
    pl.tick()
    assert video.closed and pl.in_interstitial and r.setup.name == "i"
    now[0] = 360.0
    pl.tick()
    assert pl.current == Item("setup", "a") and r.setup.name == "a"
    r.release()


def test_skip_key_also_goes_through_the_interstitial(ctx, tmp_path):
    now = [0.0]
    r, pl = _between(ctx, tmp_path, [Item("setup", "a"), Item("setup", "b")], now)
    pl.next()
    pl.next()
    assert pl.in_interstitial
    pl.next()
    assert not pl.in_interstitial and pl.current.name in ("a", "b")
    r.release()


def test_single_item_alternates_with_interstitial(ctx, tmp_path):
    now = [0.0]
    r, pl = _between(ctx, tmp_path, [Item("setup", "a")], now)
    pl.next()
    now[0] = 300.0
    pl.tick()
    assert pl.in_interstitial
    now[0] = 330.0
    pl.tick()
    assert pl.current == Item("setup", "a") and r.setup.name == "a"
    r.release()


def test_missing_interstitial_is_skipped(ctx, tmp_path):
    now = [0.0]
    r, pl = _between(ctx, tmp_path, [Item("setup", "a"), Item("setup", "b")], now, interstitial="gone")
    pl.next()
    first = pl.current
    pl.next()
    assert not pl.in_interstitial and pl.current != first
    r.release()


def test_interstitial_render_failure_drops_it(ctx, tmp_path):
    now = [0.0]
    r, pl = _between(ctx, tmp_path, [Item("setup", "a"), Item("setup", "b")], now)
    pl.next()
    pl.next()
    assert pl.in_interstitial
    pl.failed(RuntimeError("boom"))
    assert pl.interstitial is None and not pl.in_interstitial
    assert pl.items == [Item("setup", "a"), Item("setup", "b")] and r.setup is not None
    pl.next()
    assert not pl.in_interstitial
    r.release()

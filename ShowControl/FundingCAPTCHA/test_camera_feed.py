"""CameraFeed: start, drain, restart, and what a restart leaves alone."""
import threading

import pytest

import camera_feed
import settings as settings_mod
from camera_feed import CameraFeed, source_from_args


class _Args:
    def __init__(self, camera=False, mock_camera=False):
        self.camera, self.mock_camera = camera, mock_camera


def test_source_from_args():
    assert source_from_args(_Args(camera=True)) == "camera"
    assert source_from_args(_Args(mock_camera=True)) == "mock"
    assert source_from_args(_Args()) is None


def test_no_camera_still_gives_a_queue_to_paint_into():
    feed = CameraFeed({}, None)
    feed.start()
    feed.queue.put({"type": "foreground", "frame": "painted"})
    assert feed.drain() == "painted"
    assert feed.drain() is None


def test_drain_returns_the_newest_frame_and_empties_the_queue():
    feed = CameraFeed({}, None)
    for frame in ("old", "newer", "newest"):
        feed.queue.put({"type": "foreground", "frame": frame})
    assert feed.drain() == "newest"
    assert feed.queue.empty()


def test_drain_keeps_a_camera_crash_in_error():
    feed = CameraFeed({}, None)
    feed.queue.put({"type": "error", "msg": "usb unplugged"})
    assert feed.drain() is None
    assert feed.error == "usb unplugged"
    feed.start()
    assert feed.error is None, "a fresh start clears the old crash"


@pytest.fixture
def fake_camera(monkeypatch):
    """A "mock" source whose thread does nothing but wait to be stopped; records each start."""
    runs: list[dict] = []

    def _read(camera, settings, out, stop, reseed):
        runs.append({"out": out, "stop": stop, "reseed": reseed})
        stop.wait(5.0)

    monkeypatch.setattr(camera_feed, "CV_AVAILABLE", True)
    monkeypatch.setattr(camera_feed, "make_camera", lambda settings, source: object())
    monkeypatch.setattr(camera_feed, "_read_camera", _read)
    return runs


def _wait_for(runs, n):
    deadline = threading.Event()
    for _ in range(200):
        if len(runs) >= n:
            return
        deadline.wait(0.01)
    raise AssertionError(f"camera thread {n} never started")


def test_restart_stops_the_running_thread_and_starts_a_fresh_one(fake_camera):
    feed = CameraFeed({}, "mock")
    feed.start()
    _wait_for(fake_camera, 1)
    first_queue = feed.queue

    feed.restart()
    _wait_for(fake_camera, 2)

    assert fake_camera[0]["stop"].is_set(), "the running camera thread must be told to stop"
    assert not fake_camera[1]["stop"].is_set(), "a fresh camera must be running"
    assert feed.queue is not first_queue, "frames from before the restart must not reach the new run"
    assert fake_camera[1]["out"] is feed.queue
    feed.stop()


def test_reseed_reaches_the_running_thread(fake_camera):
    feed = CameraFeed({}, "mock")
    feed.start()
    _wait_for(fake_camera, 1)
    feed.reseed()
    assert fake_camera[0]["reseed"].is_set()
    feed.stop()


def test_restart_leaves_local_settings_untouched(tmp_path, monkeypatch):
    """POST /api/restart restarts the camera and leaves the per-host settings override alone."""
    local = tmp_path / "captcha-settings.local.json"
    local.write_bytes(b'{"camera": {"serial": "ABC123"},\n "attract_dwell_s": 2}\n')
    before = local.read_bytes()
    monkeypatch.setattr(settings_mod, "SETTINGS_LOCAL", local)

    CameraFeed({}, None).restart()

    assert local.read_bytes() == before


def test_restart_does_not_create_a_local_settings_file(tmp_path, monkeypatch):
    local = tmp_path / "captcha-settings.local.json"
    monkeypatch.setattr(settings_mod, "SETTINGS_LOCAL", local)
    CameraFeed({}, None).restart()
    assert not local.exists()


def test_a_camera_without_cv_libraries_exits_with_instructions(monkeypatch):
    monkeypatch.setattr(camera_feed, "CV_AVAILABLE", False)
    with pytest.raises(SystemExit, match="CV libraries not available"):
        CameraFeed({}, "camera")

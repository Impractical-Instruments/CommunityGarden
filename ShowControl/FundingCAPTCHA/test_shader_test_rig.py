"""The shader test rig's own helpers: GLSL constants, mask builders, and Rig snapshots."""
from pathlib import Path

import pytest

from shader_test_rig import BODY, EMPTY, Consts, Rig, flailing, flickering, glsl_consts, rect, standing, walking


def _common(tmp_path, src: str):
    (tmp_path / "common.glsl").write_text(src)
    return tmp_path


def test_glsl_consts_evaluates_arithmetic_earlier_constants_and_vectors(tmp_path):
    k = glsl_consts(_common(tmp_path, """
        const float A = 2.0, B = A * 3.0 - 1.0;   // B = 5
        const int N = int(max(2.0, B));
        const vec3 PAPER = vec3(0.5, 1.0, 0.25);
        const float C = -ceil(B / 2.0);
    """))
    assert (k["A"], k["B"], k["N"], k["C"]) == (2.0, 5.0, 5, -3)
    assert k["PAPER"] == (0.5, 1.0, 0.25)


def test_glsl_consts_ignores_comments_and_what_is_not_a_number(tmp_path):
    k = glsl_consts(_common(tmp_path, """
        // const float GONE = 1.0;
        const vec3 RAINBOW[2] = vec3[2](vec3(1.0), vec3(0.0));
        const vec3 INK = vec3(17.0, 17.0, 17.0) / 255.0;
        const float KEPT = 4.0;
    """))
    assert dict(k) == {"KEPT": 4.0}
    with pytest.raises(KeyError, match="GONE"):
        k["GONE"]


def test_glsl_consts_does_not_run_code(tmp_path):
    k = glsl_consts(_common(tmp_path, "const float EVIL = __import__('os').getpid();"))
    assert "EVIL" not in k and isinstance(k, Consts)


def test_the_shipped_setups_constants_are_readable():
    k = glsl_consts(Path(__file__).parent / "shaders" / "watering_can")
    assert k["LEAVE_S"] > 0


def test_rect_is_clipped_to_the_top_and_left_edges():
    m = rect(-3, -3, 2, 2)
    assert m.shape == BODY[::-1] and m.sum() == 4 and m[0, 0] and not m[2, 2]


def test_mask_builders_make_one_mask_per_camera_frame():
    for frames in (standing(5), walking(5), flailing(5), flickering(5)):
        assert len(frames) == 5 and all(f.shape == EMPTY.shape and f.dtype == bool for f in frames)
    assert not EMPTY.any()


def test_flickering_is_reproducible_and_flickers():
    a, b = flickering(10, seed=3), flickering(10, seed=3)
    assert all((x == y).all() for x, y in zip(a, b))
    assert any((x != a[0]).any() for x in a[1:])


def test_restored_rig_carries_on_as_a_fresh_one_would(ctx):
    # Setup tests share a grown Rig and restore() it between tests. A test that ran it further must not leak
    # into the next: buffers, clock and tracker all go back. watering_can reads all three.
    setup = Path(__file__).parent / "shaders" / "watering_can"

    def grown():
        rig = Rig(ctx, setup, (128, 72))
        rig.run(standing(20))
        return rig

    def state(rig):
        rig.r.draw_deferred_image()
        return [rig.r.snapshot(), rig.t]

    shared, fresh = grown(), grown()
    try:
        snap = shared.snapshot()
        shared.run([EMPTY] * 10 + flailing(5))     # the "previous test" dirties it
        shared.restore(snap)
        for rig in (shared, fresh):                # and both carry on identically, tracker included
            rig.run(walking(3) + [EMPTY] * 3)
        assert all(a == b for a, b in zip(state(shared), state(fresh), strict=True))
    finally:
        shared.release(); fresh.release()

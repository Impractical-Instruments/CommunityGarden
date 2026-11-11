"""Shared fixtures for the FundingCAPTCHA tests."""
import os

import pytest


@pytest.fixture(scope="session")
def ctx():
    """One headless OpenGL context for the whole run: creating one costs ~2 s, and every GL test file needs it.

    Tests release what they create (Renderers, textures) so nothing leaks into the next file.
    """
    moderngl = pytest.importorskip("moderngl")
    for kw in ({"backend": "egl"}, {}):
        try:
            c = moderngl.create_standalone_context(**kw)
            break
        except Exception:
            continue
    else:
        if os.environ.get("CI"):
            pytest.fail("no headless OpenGL context in CI — GL tests would silently skip")
        pytest.skip("no headless OpenGL context")
    yield c
    c.release()

# ADR 0009 — ArUco auto-layout for Flower Bed modules

**Status:** Superseded by [ADR-0015](0015-flowerbeds-gui-layout-tool.md)

**Decided:** A printed ArUco marker at each flower module's registration point was detected by the overhead camera's colour sensor, and the detected positions and yaws were written to a `layout_calibrated.json` that overrode `settings.json` at startup.

**Replaced by:** ADR-0015's browser layout tool, which writes `coordinator.modules[]` in `settings.json` directly. The marker code, the override file and the OpenCV dependency were deleted.

The full text is in git history.

# FundingCAPTCHA uses three-corner orthographic projection for Screen mapping

**Status:** Superseded by [ADR-0013](0013-fundingcaptcha-silhouette-body-interaction.md)

**Decided:** An operator touched three corners of the Screen at setup. `ScreenProjector` used them to project each touch blob onto the Screen plane and into a grid cell.

**Replaced by:** ADR-0013 removed the Screen plane, the corner calibration and `ScreenProjector`. The camera faces Players, and `apply_cam_transform()` in `silhouette.py` maps camera pixels to display pixels.

The full text is in git history.

# FundingCAPTCHA uses depth-primary touch detection with calibrated background

**Status:** Superseded by [ADR-0013](0013-fundingcaptcha-silhouette-body-interaction.md)

**Decided:** Players touched the projected Screen. The depth camera sat with the projector and found a hand as a blob nearer than a background captured while the projector showed black, because the projector's IR corrupted a background captured over content.

**Replaced by:** ADR-0013 turned the camera to face Players and reads body silhouettes, so there is no touch detection. One rule survives: a pixel with no background depth is never foreground (ADR-0023).

The full text is in git history.

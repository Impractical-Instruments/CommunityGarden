# FundingCAPTCHA uses depth-only background subtraction for touch detection

FundingCAPTCHA reuses IIVision's existing depth-based background subtraction pipeline for Screen touch detection. The Screen surface calibrates as the background; a hand touching it appears as a foreground blob 1–5 cm shallower than the background plane.

RGB subtraction (subtracting the projected image from the camera's colour image to isolate hands) was considered and rejected. The complications outweigh the benefits: projector and camera optical axes differ and require stereo calibration to align; any lag between projected frame and captured frame produces subtraction artefacts everywhere; dark projected regions make colour detection unreliable in those zones.

The Orbbec depth sensor uses near-IR and is independent of the visible-light projected image, so the projected content does not interfere with depth measurements. At ~3 feet range the camera has sufficient depth resolution to detect a hand at the screen surface.

## Consequences

IIVision blob parameters (minimum blob area, depth threshold) must be tuned for close-range hand detection rather than room-scale people detection. If hardware testing reveals that depth-only detection is unreliable at this range, RGB subtraction can be revisited — but start with depth-only.

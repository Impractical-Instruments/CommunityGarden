# FundingCAPTCHA uses depth-primary touch detection with calibrated background

> **Superseded by ADR-0013.** Camera now faces Players; body silhouette interaction replaces touch detection.

FundingCAPTCHA reuses IIVision's depth-based background subtraction pipeline for screen touch detection. The screen surface is calibrated as the background; a hand touching it appears as a foreground blob closer than the background plane by more than the detection threshold.

## Calibration must run with a black projected frame

The BenQ LH830ST laser projector emits IR that partially saturates the Orbbec's 850 nm structured-light sensor. If the projector is displaying content during background calibration, the captured background depth is corrupted in the illuminated regions — causing live touches to show negative depth delta (hand appears farther than background) and thus be missed.

The unified app (`app.py`) renders a solid black frame during `BG_CAL` state, ensuring the projector emits no content and the Orbbec gets a clean, uncontaminated background model. Calibration must not be triggered while the projector is displaying content from any other source.

## Depth dropout pixels are unknown, not foreground

The IIVision `BlobTracker` previously treated pixels with no background depth reading (`~valid_mask`) as foreground on the grounds that an unobserved pixel might be occluded. At room scale this is reasonable; at screen-touch scale with a projector running, projector-induced depth dropouts are common and cause phantom touches.

The `fg_from_invalid` branch has been removed. Pixels without a valid background depth reading are treated as unknown and excluded from foreground detection.

## Detection threshold

`depth_delta_mm` is set to 25 mm. This is above the Orbbec's typical structured-light noise floor at ~90 cm (~5–15 mm) while remaining well below the minimum hand-contact delta (~20 mm at the surface). Per-pixel adaptive thresholding via IQR noise floor (already in `BlobTracker`) provides additional suppression of noisy pixels.

## RGB subtraction rejected

Subtracting the projected image from the camera's colour image to isolate hands was considered and rejected. The complications outweigh the benefits: projector and camera optical axes differ and require stereo calibration to align; any lag between projected frame and captured frame produces subtraction artefacts everywhere; dark projected regions make colour detection unreliable in those zones.

## IR amplitude masking (future option)

If depth-primary detection proves insufficient after the calibration and threshold fixes above, the Orbbec's left IR stream (`OBSensorType.LEFT_IR_SENSOR`) can be enabled alongside depth. Pixels with IR amplitude above a saturation threshold (~50 000 in Y16) indicate projector interference; masking those pixels in `_subtract_background` before foreground computation provides an additional layer of robustness. This is deferred until the simpler fixes are validated in practice.

## Consequences

- `BlobTracker._subtract_background()` does not treat depth-dropout pixels as foreground.
- `depth_delta_mm` in `captcha-settings.json` is set to 25 (was 10).
- `app.py` renders black during `BG_CAL`; operator must not manually override the projector source during calibration.
- IIVision blob parameters (`min_blob_pixels`, `depth_delta_mm`) remain tuned for close-range hand detection rather than room-scale people detection.
- If hardware testing reveals depth-primary detection is still unreliable, IR amplitude masking can be added without changing the overall architecture.

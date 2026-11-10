# FundingCAPTCHA learns its depth background continuously — no boot-time standback

**Supersedes:** the BG_CAL section of [ADR-0013](0013-fundingcaptcha-silhouette-body-interaction.md)
**Amends:** [ADR-0021](0021-fundingcaptcha-shader-player.md) (startup consequence)

## Context

Every launch of `app.py`, `shader_app.py` (and `playlist_app.py`, which shares its camera), and `body_grid_tester.py` ran BG_CAL: a `calibration_standback_s` hold-off, then `calibration_frames` frames into IIVision's `Calibrator`, which built a fixed per-pixel median background. The floor had to be clear for that whole time. Anyone standing in front of the camera was baked into the background until the next restart. That cost hit every time we switched between the game app and the shader player, or restarted either.

**A saved background (`Calibration.save()` / `.load()`) was rejected.** It goes stale whenever things get moved or the camera gets bumped, and then someone has to remember to recalibrate.

**Motion detection was rejected.** It loses anyone who stands still, and Watering can rewards exactly that.

## Decision

FundingCAPTCHA uses `IIVision.AdaptiveBackground`: **the farthest steady depth wins.** A person can only make a depth pixel nearer, never farther, so each pixel's background is the farthest depth it has held steadily. It is learned continuously from the first frame, with people in view.

Per pixel, all vectorised numpy, with `thr = max(depth_delta_mm, noise_k × σ)`. Samples below 50 mm, including 0 (no return), are ignored.

0. **Warm-up.** The first `warmup_s` of a stream are ignored. Measured on the Gemini 336: the first frames read up to ~400 mm too far (1 frame when warm, ~5 from cold). Seeding from them made the true surface look nearer, leaving little blobs that lasted until `absorb_s`.
1. **Seed.** `bg` and σ are the mean and standard deviation of the first `min_valid_frames` valid samples, and the pixel is trusted (`valid`) after them. Seeding from a single sample is fragile: on a noisy far pixel (σ ≈ 80 mm at 3.7 m), one far outlier left every later reading "nearer", so the pixel was always foreground, never at background, and too jumpy to be absorbed.
2. **At background** (`|d − bg| ≤ thr`). A slow EMA moves `bg` toward `d` (`bg_alpha`). An EMA of `|d − bg| / 0.8` tracks σ (`noise_alpha`). Mean absolute deviation is about 0.8σ.
3. **Farther** (`d > bg + thr`) for `reveal_frames` frames in a row. `bg` becomes the mean of those samples. One frame that isn't farther resets the run, so flying pixels and multipath spikes can't push `bg` out.
4. **Nearer** (`d < bg − thr`, which is foreground), holding steady within `thr`, for `absorb_s`. Then `bg = d`. This covers a dropped bag or a moved table. Any jump resets the timer.
5. **Bump guard.** If more than `reseed_fg_fraction` of valid pixels stay foreground for `reseed_after_s`, `bg` is reseeded from the current frame and a warning is logged. Shifts farther heal through rule 3 with no reseed.

Foreground is computed exactly as before, by `BlobTracker._subtract_background`: the pixel is in range, `valid`, and nearer than `bg` by more than the model's threshold. Despeckling is unchanged. `BlobTracker` now reads a small `BackgroundModel` protocol (`background`, `valid_mask`, `threshold(depth_delta_mm)`). Both `Calibration` and `AdaptiveBackground` implement it. `Calibrator` stays, and FlowerBeds (`IIVision.pipeline`) still uses it.

Tunables live in `captcha-settings.json` → `background`. `detection.depth_delta_mm` remains the lower bound on `thr`.

| setting | default | note |
|---|---|---|
| `warmup_s` | 1.0 | covers the Gemini 336's cold-start frames plus settling |
| `min_valid_frames` | 10 | about 0.7 s at 15 fps |
| `reveal_frames` | 5 | |
| `noise_k` | 4 | about the old 3×IQR threshold |
| `bg_alpha` | 0.01 | per frame |
| `noise_alpha` | 0.05 | per frame |
| `absorb_s` | 300 | **must stay above 120** (Watering can) |
| `reseed_fg_fraction` | 0.4 | of valid pixels |
| `reseed_after_s` | 30 | |
| `stats_log_s` | 30 | how often per-frame update time is logged |

## Behaviour

- **Floor empty at boot.** Live as soon as pixels become valid: `warmup_s` plus `min_valid_frames`, about 2 s. There is no countdown or standback screen in any entry point.
- **Someone standing at boot.** They're invisible until they move. One step reveals the background behind them, and from then on they're tracked.
- **A spot nobody ever uncovers.** It's never learned, and it's never falsely marked foreground either.
- **Someone still for longer than `absorb_s`.** They're absorbed into the background, and they reappear when they move (rule 3).
- **`R` in `app.py` and `body_grid_tester.py`** reseeds the background from the next frame. `/api/restart` still restarts the camera thread, which starts a fresh model.

## Consequences

- `calibration_frames`, `calibration_countdown_s` and `calibration_standback_s` are removed from `captcha-settings.json`. So are the BG_CAL state and the `cal_progress` / `cal_done` camera messages.
- The model is never saved to disk. Each boot learns again from the first frame.
- Per-frame update time is logged every `stats_log_s`: 12–14 ms mean (24 ms max) at 640×480 with the live Orbbec on the show PC, against a 66 ms frame budget at 15 fps.
- Pixels with no valid background (open space beyond range) stay never-foreground, as before. Treating "no return" as infinitely far would be a separate change.
- The model learns while the projector shows content. ADR-0004's black-frame-during-calibration rule came from the touch-screen setup that ADR-0013 removed; the camera now faces visitors, not the screen.
- To check on hardware: the update time stays within the frame budget on the show machine; `absorb_s` suits real dwell times; and a dense crowd doesn't set off the bump guard. After a reseed the crowd becomes background, then heals as people leave. If that's not acceptable, require a scene-wide depth shift as well.

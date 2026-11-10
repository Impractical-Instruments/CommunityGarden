# ADR 0024 — Shader player image channel: one shuffled image per load

**Status:** Accepted
**Amends:** [ADR-0021](0021-fundingcaptcha-shader-player.md)

## Context

ADR-0021 lets Setups use only procedural content and the Body: "Shadertoy can't take uploaded media." The Watercolor Smudge Setup ([spec](../superpowers/specs/2026-11-07-watercolor-smudge-design.md), issue #164) smears and heals a watercolor painting. Painted watercolors look far better than procedural watercolor-ification. They get wet edges, blooms and granulation for free, while a filter reads as a photo-app effect. The artist will supply a set of paintings, and each time the Setup plays it should show a different one.

## Decision

1. **A new channel source, `"image"`.** It's bound like any other source in `setup.json`. It binds one image from the Setup's own `images/` folder (`.png`, `.jpg`, `.jpeg`, any case; other files are ignored). The texture is RGBA8, linear-filtered and clamped like every channel, with no mipmaps. `iChannelResolution` reports its size in pixels.

2. **One image per load, shuffled.** `shader_app.SetupImages` (used by both `shader_app.Rotation` and `playlist_app.Playlist`) keeps one `arc.ShuffleBag` of image paths per Setup for the whole run. It draws the next one on every real load, so no image repeats until all have shown.
   - **R** (hot reload) is a real load and advances the bag.
   - A Setup that's the only one playing (`--setup NAME`, or a one-entry `setups.json`) isn't reloaded when its `duration_s` runs out (ADR-0021), so it keeps its image.
   - If the folder's file list changes, the bag is rebuilt on the next load.

3. **Decoding.** Images are decoded on load with Pillow into RGBA with row 0 at the bottom (GL, matching the Body), turned upright per their EXIF orientation (phone photos). Before upload, an image is downscaled, keeping aspect and never upscaled, to the smallest size that still *covers* the window, since Setups cover-fit it. No side may exceed `GL_MAX_TEXTURE_SIZE`.

4. **No images is not an error.** With an empty or missing `images/` folder, the source is unbound: it reads 0 and `iChannelResolution[n]` is `(0, 0, 0)`. A Setup can test `iChannelResolution[n].x == 0.0` and fall back to something procedural. CI and fresh clones play such Setups normally.

5. **Broken files are skipped.** A file that won't decode is logged and dropped from that Setup's bag for the run, and the next is tried. If none decode, the Setup plays with the source unbound.

6. **Prototyping.** Shadertoy can't take uploads, so prototype with one of its built-in textures in that channel. Hand-in writes `"image"` where Shadertoy has the texture.

## Consequences

- Image files live in the public repo next to the Setup that uses them. Nothing private may go there (see `docs/FundingCAPTCHA.md`).
- Pillow, already a dependency, is now used by `shader_app.py`.
- Decoding happens at load time, on the render thread. A large JPEG adds a visible hitch at the Setup change. Keep images near display size.
- Only one image per Setup per load. A Setup that wants several images at once would need another amendment.

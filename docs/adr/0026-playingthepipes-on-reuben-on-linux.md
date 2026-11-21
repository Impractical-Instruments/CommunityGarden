# ADR 0026 — Playing the Pipes runs on reuben, on Linux

**Status:** Accepted
**Amends:** [ADR-0014](0014-playingthepipes-encoder-picos.md) (the host and the serial reader; the Picos and their protocol are unchanged)

*Note, 2026-11-18: decided and built (#177, #236–#239), but not yet run on the show box. Decision 6 (how reuben reaches the audio interface at boot) is the part still to be confirmed there (#235).*

*Note, 2026-11-20: decision 5 says reuben `main`. The CI check (`.github/scripts/check-reuben-pin.sh`) requires the pinned commit to be on reuben `dev`, its integration branch; `main` there is the release branch.*

*Note, 2026-11-21: decision 2 says Ubuntu Desktop on a mini PC. The box is a Raspberry Pi 5 running Raspberry Pi OS with desktop on Debian 13. Everything else in decision 2 holds: systemd units, `deploy/install.sh`, `scripts/deploy.sh`. Decision 6 carries over unchanged, since that image runs PipeWire in the user's session the same way.*

## Context

The Playing the Pipes audio engine was a Max 9 patch on a Windows mini PC. Max was opened by hand after boot; it could not run as a service, so the health endpoint could be green while there was no sound. The patch depended on a third-party package and on Max 9's bundled devices, the two encoder Picos needed their COM ports pinned in Device Manager, and nothing about the patch could be tested in CI. The box was the only show machine that was not Linux, so it had its own provisioning, its own service manager (NSSM) and a manual deploy.

reuben is our own open-source audio engine (Impractical-Instruments/reuben): a headless program that plays an instrument described in a JSON document and takes control over OSC.

## Decision

1. **reuben replaces Max.** The engine is the instrument `ShowControl/PlayingThePipes/reuben/pipes.json`, played by `reuben play`. `make validate-instruments` load-checks it in CI.

2. **The box runs Linux (Ubuntu Desktop), moved at the same time as the engine.** It is provisioned and deployed like the other show machines: systemd units, `deploy/install.sh`, `scripts/deploy.sh`. We did not port to Windows first.

3. **There is no Max fallback on the box.** Max does not run on Linux. The Max project stays in the repo only as the reference for a by-ear A/B on a laptop, and is deleted after sign-off.

4. **A Python bridge sits between the Picos and reuben.** `encoder_bridge.py` reads the Picos (found by USB vendor ID `2E8A`, any port, reconnecting on replug), computes every knob and loop value in `pipes_control.py`, and sends them to reuben as OSC. The knob behaviour (velocity, wake, idle, the loop mix) lives in Python, tuned by `settings.json`; the instrument only makes sound. The bridge also serves `/health`, which reports the Picos and whether reuben is alive.

5. **reuben is a submodule at `vendor/reuben`, built from source, on the box too.** No release binaries. While iterating, the submodule can point at any commit; a PR merges only if the pinned commit is on reuben `main` (CI check). A deploy pushes the pinned commit to the box over ssh, so the box never fetches reuben from GitHub.

6. **Two system units, with reuben pointed at the service user's PipeWire.** `pipes-reuben` and `pipes-bridge` run as `ii`. On the desktop OS (see the 2026-11-21 note) PipeWire owns the audio interface and runs in a user's session, so the installer enables lingering for `ii` (its session starts at boot with nobody logged in) and `pipes-reuben` reaches it through `XDG_RUNTIME_DIR`.

7. **The mic's spectral freeze became a pre-delay plus a feedback echo.** reuben has nothing like Max's `spectraltime~`. The mic goes through a pre-delay (0.5 s left, 0.75 s right) into a feedback delay. The pre-delay is what prevents feedback through the speakers.

8. **The limiter is a compressor at about 20:1 with a fast attack, then a hard clamp at ±1.** reuben has no brickwall limiter.

## Reasons

- **A service, not an application someone opens.** reuben starts at boot, restarts on failure, and its liveness is in `/health`.
- **One provisioning and deploy path for every show machine.** Moving to Linux removed NSSM, COM port pinning, the Windows bootstrap section and the manual deploy. Doing it together with the engine port avoided building Windows service and deploy tooling that would be thrown away.
- **Knob behaviour in Python is testable.** `test_pipes_control.py` covers it without audio, and fails if the bridge sends an address the instrument has no pipe for. The first design put this logic in the instrument, which would have needed new reuben operators and could only be checked by ear.
- **Building from source keeps reuben changes one commit away.** We develop reuben alongside the show; a fix can be pinned and deployed from a laptop at a venue with no release step and no internet.

## Consequences

- **Rust is needed** on the box and on any machine that runs `make pipes`. A deploy that changes reuben rebuilds it on the box, which is slower than a Python-only deploy.
- **An offline deploy cannot carry everything.** A new crate, a toolchain change, or a new sample (Git LFS) needs internet on the box once. The installer stops before restarting anything when one is missing (`docs/PlayingThePipes.md`).
- **The box needs a device profile** (`reuben/pipes.profile.json`) for its audio interface. Changing the interface means changing that file.
- **reuben's ports are fixed** (OSC on 9000, structure on 9124). `network.json` records them and a test keeps them in step with `vendor/reuben`.
- **The bridge-to-instrument OSC addresses are a contract** between `pipes_control.py` and `reuben/pipes.json` (`docs/osc-fabric.md`). They are not part of the OSC Fabric.
- **The instrument is not identical to the Max patch.** The differences, some of them fixes, are listed in `ShowControl/PlayingThePipes/README.md`. Sign-off is by ear.
- **Until sign-off the samples stay in `Lamplight2026/media/`**, inside the Max project.

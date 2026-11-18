# Architecture decision records

One file per decision, numbered in the order they were made. Take the next free number for a new one, and add its row here.

The first line under each title is its status:

- **Accepted**: in force as written.
- **Accepted and amended by N**: in force, except where ADR N says otherwise. Read both.
- **Partially implemented**: decided, but only part was built. A dated note at the top says which part.
- **Superseded by N**: no longer in force. The file keeps only what was decided and what replaced it; git history has the rest.

A dated note (*Note, 2026-11-18: …*) corrects a name or fact that changed after the decision. The decision text itself is left as written.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-osc-as-cross-element-communication.md) | OSC as the cross-element communication fabric | Accepted and amended by [ADR-0007](0007-osc-fabric-schema.md) |
| [0002](0002-dwell-is-cluster-local-not-global-blob-lifetime.md) | Dwell is tracked per-cluster, not exported from BlobStabilizer | Accepted |
| [0003](0003-all-fundingcaptcha-games-must-self-terminate.md) | All FundingCAPTCHA games must self-terminate on inactivity | Accepted |
| [0004](0004-fundingcaptcha-uses-depth-only-touch-detection.md) | FundingCAPTCHA uses depth-primary touch detection with calibrated background | Superseded by [ADR-0013](0013-fundingcaptcha-silhouette-body-interaction.md) |
| [0005](0005-branch-controller-uses-usb-serial-not-ethernet.md) | Branch controller uses USB serial, not Ethernet | Accepted |
| [0006](0006-two-tier-controllable-hierarchy.md) | Two-tier Controllable hierarchy (Controllable / LEDControllable) | Accepted and amended by [ADR-0020](0020-treehouse-esp32s3-location-controllers.md) |
| [0007](0007-osc-fabric-schema.md) | OSC Fabric message schema | Accepted (amended in place 2026-11-11) |
| [0008](0008-gardenstate-display-expression-mapping.md) | GardenState → display expression mapping | Partially implemented |
| [0009](0009-aruco-auto-layout-for-flower-modules.md) | ArUco auto-layout for Flower Bed modules | Superseded by [ADR-0015](0015-flowerbeds-gui-layout-tool.md) |
| [0010](0010-treehouse-led-pico-architecture.md) | TreeHouse LED driver: two MicroPython Picos with PIO | Superseded by [ADR-0020](0020-treehouse-esp32s3-location-controllers.md) |
| [0011](0011-fundingcaptcha-screen-calibration-and-projection.md) | FundingCAPTCHA uses three-corner orthographic projection for Screen mapping | Superseded by [ADR-0013](0013-fundingcaptcha-silhouette-body-interaction.md) |
| [0012](0012-fundingcaptcha-unified-pygame-app.md) | FundingCAPTCHA runs as a unified pygame app | Accepted and amended by [ADR-0013](0013-fundingcaptcha-silhouette-body-interaction.md) and [ADR-0023](0023-fundingcaptcha-self-learning-depth-background.md) |
| [0013](0013-fundingcaptcha-silhouette-body-interaction.md) | FundingCAPTCHA uses body silhouette interaction, not touch detection | Accepted and amended by [ADR-0023](0023-fundingcaptcha-self-learning-depth-background.md) |
| [0014](0014-playingthepipes-encoder-picos.md) | Playing the Pipes uses Pi Pico encoder boards, not direct Pi GPIO | Accepted |
| [0015](0015-flowerbeds-gui-layout-tool.md) | FlowerBeds GUI Layout Tool | Accepted |
| [0016](0016-fundingcaptcha-test-input-mode.md) | FundingCAPTCHA `--test-input` mode for camera-free game development | Accepted and amended by [ADR-0023](0023-fundingcaptcha-self-learning-depth-background.md) |
| [0017](0017-club-diorama-rave-screen.md) | Club Diorama Rave Screen | Accepted |
| [0018](0018-pygame-weston-dual-display.md) | pygame/SDL2 + weston for dual-display rendering | Accepted |
| [0019](0019-fundingcaptcha-game-ui-shell.md) | FundingCAPTCHA Games share a single UI shell — billboard prompt + maximal grid | Accepted |
| [0020](0020-treehouse-esp32s3-location-controllers.md) | TreeHouse lighting: one ESP32-S3 per location, driven by Garden State | Accepted and amended by [ADR-0021](0021-treehouse-controllers-standalone-and-garage-welder.md) |
| [0021](0021-treehouse-controllers-standalone-and-garage-welder.md) | TreeHouse controllers run standalone; a fifth controller welds in the Garage | Accepted |
| [0022](0022-shader-player-blob-records.md) | Shader player blob records: boxes, stable IDs, lifecycle | Accepted |
| [0023](0023-fundingcaptcha-self-learning-depth-background.md) | FundingCAPTCHA learns its depth background continuously — no boot-time standback | Accepted |
| [0024](0024-shader-player-image-channel.md) | Shader player image channel: one shuffled image per load | Accepted |
| [0025](0025-fundingcaptcha-shader-player.md) | FundingCAPTCHA shader player — Shadertoy Setups driven by the depth camera | Accepted and amended by [ADR-0022](0022-shader-player-blob-records.md), [ADR-0023](0023-fundingcaptcha-self-learning-depth-background.md), [ADR-0024](0024-shader-player-image-channel.md) |

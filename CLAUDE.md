# CLAUDE.md — CommunityGarden

AI assistant guide for the **CommunityGarden** codebase — show control software for the interactive flower installation at [Connect Beyond Festival](https://www.connectbeyondfestival.com/).

---

## Project Overview

This is an **Unreal Engine 5** show control system that uses computer vision (Orbbec depth camera) to detect people and drive physical flower servo motors in response. The system:

1. Captures depth frames from an Orbbec camera
2. Detects human-presence blobs in 3D space via the `IIVision` plugin
3. Maps blobs to nearby flower clusters
4. Sends OSC messages over Ethernet to Arduino motor controllers
5. Arduino controllers drive Dynamixel servos to rotate physical flowers toward detected people

---

## Repository Structure

```
CommunityGarden/
├── FlowerBeds/                    # Main Unreal Engine 5 project
│   ├── FlowerBeds.uproject        # UE5 project file (EngineAssociation: "UE-II")
│   ├── Config/                    # UE config files (INI)
│   │   ├── DefaultGame.ini        # Runtime settings: controllers, modules, blob trackers
│   │   ├── DefaultEngine.ini      # Rendering, map, engine settings
│   │   ├── DefaultInput.ini       # Input bindings
│   │   └── DefaultEditor.ini      # Editor preferences
│   ├── Content/                   # UE assets (Blueprints, Maps, Materials) — tracked via Git LFS
│   ├── Source/
│   │   └── FlowerBeds/            # Main C++ game module
│   │       ├── FlowerBeds.Build.cs
│   │       ├── FlowerBedCoordinator.h/.cpp   # Top-level orchestrator Actor
│   │       ├── FlowerBedSettings.h           # UDeveloperSettings — config entry point
│   │       ├── OrbbecBlobTracker.h/.cpp      # Actor: camera input + blob detection
│   │       ├── FlowerModule.h/.cpp           # Actor: physical module with clusters
│   │       ├── FlowerCluster.h/.cpp          # Actor: individual cluster driving one motor
│   │       ├── FlowerController.h/.cpp       # UObject: OSC client for one controller board
│   │       ├── OrbbecToVisionHelpers.h/.cpp  # Data conversion utilities
│   │       └── LookCoordinator.h/.cpp        # Gaze/attention direction logic
│   └── Plugins/
│       ├── IIVision/              # Impractical Instruments blob-tracking library
│       ├── OrbbecSensor/          # Orbbec SDK wrapper (Win64 only; delay-loads OrbbecSDK.dll)
│       └── RiderLink/             # JetBrains IDE integration (pre-included, disabled by default)
├── Firmware/
│   ├── FlowerBeds_Follow_ServoController/   # Arduino sketch: receives OSC → drives Dynamixel servos
│   └── Dynamixel_Config/                   # Arduino sketch: one-time Dynamixel ID/baud configuration
├── Scripts/
│   └── InstalledEngineBuild.ps1   # PowerShell: builds a Win64 UE Installed Build from source
├── TouchOSC/
│   └── FlowerBedTester.tosc       # TouchOSC layout for manual motor testing
├── .gitattributes                 # Git LFS rules for UE binary assets
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Game engine | Unreal Engine 5 (`UE-II` — custom installed build) |
| Primary language | C++ (UE conventions) |
| Build system | Unreal Build Tool (UBT) + `.Build.cs` files |
| Computer vision | Custom `IIVision` plugin (blob detection from depth frames) |
| Depth camera | Orbbec SDK v2 via `OrbbecSensor` plugin |
| Networking | OSC over UDP (UE `OSC` module + Arduino `OSCMessage` library) |
| Motor hardware | Dynamixel servos via `Dynamixel2Arduino` library |
| Microcontroller | OpenRB-150 (SAMD21) running Arduino firmware |
| Control UI | TouchOSC layout for manual testing |
| Build scripts | PowerShell (Windows only) |

---

## C++ Code Conventions

This project follows standard Unreal Engine C++ conventions throughout.

### Naming Prefixes

| Prefix | Meaning |
|---|---|
| `A` | Actor subclass (e.g., `AFlowerBedCoordinator`, `AFlowerModule`) |
| `U` | UObject subclass (e.g., `UFlowerController`, `UFlowerBedSettings`) |
| `F` | Plain struct (e.g., `FFlowerClusterConfig`, `FFlowerControllerConfig`) |
| `I` | Interface |
| `T` | Template class |

### UPROPERTY / UFUNCTION Macros

- Use `UPROPERTY(EditAnywhere, Config, Category = "Flower Beds")` for settings that should be editable in-editor and persisted to INI.
- Use `UPROPERTY(Transient)` for runtime-only objects that should not be serialized (e.g., spawned actors, OSC clients).
- Use `UFUNCTION(BlueprintCallable)` for methods that may need to be called from Blueprint.
- Use `DECLARE_MULTICAST_DELEGATE_*` for native-only callbacks; use `DECLARE_DYNAMIC_MULTICAST_DELEGATE_*` for Blueprint-assignable delegates.

### Smart Pointers

- Use `TObjectPtr<UType>` for GC-tracked UObject references.
- Use `TArray<>`, `TMap<>`, etc. — never raw STL containers.
- Avoid raw pointers to UObjects; prefer `TObjectPtr` or `TWeakObjectPtr` depending on ownership.

### Logging

Use the custom log category for this project:

```cpp
UE_LOG(LogFlowerBeds, Log, TEXT("..."));
UE_LOG(LogFlowerBeds, Warning, TEXT("..."));
UE_LOG(LogFlowerBeds, Error, TEXT("..."));
```

### Header Guards

Use `#pragma once` — never `#ifndef` guards.

### Module PCH

All modules use `PCHUsage = PCHUsageMode::UseExplicitOrSharedPCHs`. Always include `CoreMinimal.h` explicitly rather than relying on PCH.

### RTTI

Both `IIVision` and `OrbbecSensor` set `bUseRTTI = true` in their `.Build.cs`. The main `FlowerBeds` module does not require RTTI.

---

## Architecture & Key Patterns

### Coordinator Pattern

`AFlowerBedCoordinator` is the top-level Actor placed in the level. On `BeginPlay` it reads settings and spawns:
- One `AOrbbecBlobTracker` per configured camera
- One `AFlowerModule` per configured physical module
- One `UFlowerController` per configured motor controller board

It subscribes to `AOrbbecBlobTracker::OnBlobDetectionResult` and routes detection results to `AFlowerModule::UpdateClusterTargets`, which in turn calls `UFlowerController::SendFlowerRotation` via OSC.

### Configuration as Data

All runtime configuration lives in `UFlowerBedSettings` (a `UDeveloperSettings` subclass, `Config=Game`). This means settings are:
- Editable in the UE Editor under **Edit → Project Settings → Flower Beds**
- Persisted to `FlowerBeds/Config/DefaultGame.ini`
- Readable at runtime via `GetDefault<UFlowerBedSettings>()`

The same pattern is used for `UBlobTrackerSettings`.

**Do not hardcode network addresses, positions, or motor IDs** — they all belong in settings structs.

### OSC Communication Flow

```
UE (FlowerController) --UDP/OSC--> Arduino (192.168.1.50:9000)
  address: /cg/ff/rot
  args:    [int motorId, float rotationDeg]
```

The Arduino firmware listens on that address and calls `setRotDeg()` to drive the target Dynamixel servo.

### Blob Detection Pipeline

```
Orbbec Camera
  → FOrbbecFrame (depth at 640×400, 30fps)
  → AOrbbecBlobTracker::OnFramesReceived()
  → OrbbecToVisionHelpers (converts to IIVision frame format)
  → II::Vision::FBlobTracker::Detect()
  → FBlobTracker::FDetectionResult (array of FBlob3D with 3D world positions)
  → AFlowerBedCoordinator::OnBlobDetectionResult()
  → AFlowerModule::UpdateClusterTargets()
  → AFlowerCluster::UpdateClusterTargets() → nearest-blob angle calculation
  → UFlowerController::SendFlowerRotation()
```

---

## Configuration Reference

### DefaultGame.ini Structure

```ini
[/Script/FlowerBeds.FlowerBedSettings]
+FlowerControllers=(IPAddress="192.168.1.50",Port=9000)
+FlowerModules=(RegistrationPointPosCm=(...),Rotation=(...),FlowerClusters=(...))

[/Script/FlowerBeds.BlobTrackerSettings]
+BlobTrackers=(Name="...",PosCm=(...),Rotation=(...),CameraConfig=(...))
```

- Use `+` prefix to append to array properties.
- `RegistrationPointPosCm` is the physical anchor point of each module in centimeters relative to the chosen world origin.
- `MotorId` in `FFlowerClusterConfig` must match the Dynamixel servo ID set via `Dynamixel_Config` firmware.
- Camera `DeviceSerialNumber` must match the serial printed on the Orbbec device.

### Network Setup

- Arduino controller default IP: `192.168.1.50`, port `9000`
- MAC address is hardcoded in firmware: `DE:AD:BE:EF:15:00`
- All devices must be on the same LAN subnet

---

## Build & Development Workflow

### Prerequisites

- Windows (Win64 is the only supported target platform)
- Unreal Engine 5 installed (engine association `"UE-II"` — see registry key for installed path)
- Visual Studio 2022 with C++ game development workload
- Arduino IDE or PlatformIO for firmware

### Opening the Project

1. Double-click `FlowerBeds/FlowerBeds.uproject` to open in UE5 Editor.
2. On first open UBT will compile the `FlowerBeds`, `IIVision`, and `OrbbecSensor` modules.
3. Generate Visual Studio solution: **File → Generate Visual Studio Project Files** or run `GenerateProjectFiles.bat`.

### Building (Editor)

Build from Visual Studio (`Development Editor` configuration, `Win64`) or use the UE toolbar.

### Building a Packaged / Installed Build

Use the provided PowerShell script to create a redistributable Win64 engine build:

```powershell
.\Scripts\InstalledEngineBuild.ps1 -EngineRoot "D:\UE\UnrealEngine"
# Optional flags:
#   -Clean              # remove previous build artifacts
#   -WithDDC $true      # include Derived Data Cache
#   -GameConfigurations @('Development','Shipping')
```

Output goes to `<EngineRoot>\Engine\LocalBuilds\Engine\Windows\`.

### Packaging the Game

Use the standard UE packaging workflow (File → Package Project → Windows) or UAT. `OrbbecSDK.dll` is automatically staged next to the executable via `RuntimeDependencies` in `OrbbecSensor.Build.cs`.

### Firmware

Open `.ino` files in Arduino IDE:

- **`FlowerBeds_Follow_ServoController`** — deploy to each OpenRB-150 controller board. Update the `ip` and `mac` variables for each board if running multiple controllers.
- **`Dynamixel_Config`** — one-time utility to configure Dynamixel servo IDs and baud rates before deployment.

Required Arduino libraries:
- `Dynamixel2Arduino`
- `Ethernet`
- `OSCMessage` (CNMAT OSC library)

---

## Content & Assets

All content is under `FlowerBeds/Content/` and tracked via **Git LFS** (`.gitattributes` rules cover `.uasset`, `.umap`, `.fbx`, `.pdb`, and other binary types).

Key assets:
- `BP_FlowerBedCoordinator` — Blueprint subclass of `AFlowerBedCoordinator`; place one in the level
- `BP_OrbbecBlobTracker` — Blueprint subclass; set `BlobTrackerClass` on the coordinator
- `BP_FlowerModule`, `BP_FlowerCluster`, `BP_Flower` — physical hierarchy
- `FlowerBeds.umap` — main production level
- `CameraTest.umap` — debug level for camera/blob visualization
- `M_DepthIRDebug`, `M_BlobOverlayDebug` — debug visualization materials

---

## No Formal Tests or CI

There is currently no automated test suite and no CI/CD pipeline. Verification is done by:
1. Running in-editor with a connected Orbbec camera and the debug maps
2. Using the `CameraTest.umap` level and debug visualizers (`UArrayVisualizer`, `UBlobArrayVisualizer`)
3. Using the TouchOSC layout (`TouchOSC/FlowerBedTester.tosc`) for manual motor validation

When making changes, manually verify the full pipeline: camera → blob detection → OSC → servo movement.

---

## Git Workflow

- **Main branch:** `main`
- **Feature branches:** use descriptive names (e.g., `claude/add-claude-documentation-QRcEL`)
- **Large binary assets** are tracked with Git LFS — never commit binaries without LFS configured
- No pre-commit hooks are installed; review changes manually before committing
- Commit messages are informal/descriptive (not conventional commits format)

```bash
git push -u origin <branch-name>
```

---

## Key Things to Know Before Making Changes

1. **Platform is Win64 only.** The `OrbbecSensor` plugin has a Win64 guard in its `.Build.cs`; do not attempt to build for other platforms.
2. **Settings are INI-driven.** Avoid adding hardcoded values for IPs, ports, positions, or motor IDs — add them to the appropriate `UDeveloperSettings` subclass instead.
3. **OSC address is `/cg/ff/rot`.** The UE side (`FlowerController.cpp`) and the Arduino firmware (`FlowerBeds_Follow_ServoController.ino`) must agree on this address. Change it in both places if needed.
4. **Dynamixel motor IDs must match config.** `FFlowerClusterConfig::MotorId` must match the ID programmed into the servo hardware.
5. **`bUseRTTI = true` is required** in `IIVision` and `OrbbecSensor` build rules — do not remove it.
6. **Do not modify `RiderLink` plugin.** It is a prebuilt JetBrains plugin; update it as a whole unit if needed.
7. **Git LFS must be active** before cloning or pulling — otherwise binary assets will be broken stubs.

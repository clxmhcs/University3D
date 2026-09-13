# Jiangcheng University / 江城大学 — University3D

SwiftUI + Unity URP 3D campus app for Jiangcheng University.

## Current engineering stage

**Stage A1 — split VM / Device acceptance.**

Frozen architecture:

- SwiftUI owns app/business UI.
- Unity URP owns the 3D world and simulation.
- CampusData is the single authoritative business-data source.
- Swift ↔ Unity communication uses permanent object IDs through CampusBridgeProtocol v1.
- Campus content will stream in 250m × 250m chunks.
- No Unity-scene manual coordinate system may become a second source of truth.

Current source override baseline: `PATCH-2026-09-12-R5`.

## Pinned Stage A1 toolchain

- Unity: **6.3 LTS / 6000.3.15f1**
- Universal Render Pipeline: **17.3.0**
- Addressables: **2.7.6**
- Input System: **1.17.0**
- iOS deployment baseline: **iOS 17.0**
- Unity iOS graphics API: **Metal only**
- Unity scripting backend: **IL2CPP**
- Bundle identifier baseline: `com.clxmhcs.University3D`

## Virtual-machine workflow

The current development environment is allowed to complete **Stage A1-VM** first:

```bash
./BuildScripts/stage_a1_prepare.sh
```

This performs Unity iOS export, unsigned UnityFramework build, unsigned SwiftUI host build, static bridge validation, and writes `.stage-a1/STAGE_A1_VM_REPORT.txt`.

A1-VM PASS allows Stage B data/tooling development to proceed.

It does **not** close Stage A. Real-device acceptance remains mandatory.

## Real-iPhone workflow

When a physical iPhone is visible to Xcode (through VM USB passthrough or a physical Mac), run:

```bash
./BuildScripts/stage_a1_device_preflight.sh
```

Then complete the manual `focusObject(TEST-01) → objectSelected(TEST-01)` bridge test on the real device.

See `Docs/Stage-A1-Acceptance.md` for the exact VM/Device closure rules.

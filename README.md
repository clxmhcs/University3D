# Jiangcheng University / 江城大学 — University3D

SwiftUI + Unity URP 3D campus app for Jiangcheng University.

## Current engineering stage

**Stage A1 — reproducible iOS host + Unity URP/iOS toolchain configuration.**

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

`Stage A1` does not yet mean the real-iPhone bridge test has passed. Run `BuildScripts/stage_a1_prepare.sh` on the Mac, then complete the signing/device acceptance documented in `Docs/Stage-A1-Acceptance.md`.

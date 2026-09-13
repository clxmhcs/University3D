# Stage A1 — VM / Device two-layer acceptance

## Source contract

Every campus-data operation continues to obey the highest-priority source override patch:

`PATCH-2026-09-12-R5`

The architecture remains unchanged:

- SwiftUI owns app/business UI.
- Unity URP owns the 3D world and simulation.
- CampusData is the single authoritative data source.
- CampusBridgeProtocol v1 is the only Swift ↔ Unity message contract.
- Production campus coordinates must never be repaired by hand inside Unity scenes.

Stage A1 is split because the current development machine is a macOS virtual machine.

## Pinned toolchain

- Unity 6.3 LTS: `6000.3.15f1`
- URP: `17.3.0`
- Addressables: `2.7.6`
- Input System: `1.17.0`
- iOS deployment target: `17.0`
- Unity build backend: IL2CPP
- Graphics API: Metal only
- Bundle ID baseline: `com.clxmhcs.University3D`

The Apple Development Team is intentionally not stored in Git.

---

## Stage A1-VM

A1-VM is the development gate for the virtual machine. It proves that the repository and iOS toolchain are structurally buildable without treating a VM as a real iPhone.

Run from repository root:

```bash
./BuildScripts/stage_a1_prepare.sh
```

`stage_a1_prepare.sh` defaults to VM mode and dispatches to `stage_a1_vm_prepare.sh`.

A1-VM performs:

1. macOS/Xcode/Python/XcodeGen/Unity prerequisite checks.
2. Environment/virtualization reporting.
3. Static Stage A/A1 validation.
4. Unity batch-mode project configuration using `-nographics`.
5. Bootstrap scene generation with `TEST-01`.
6. Unity iOS export.
7. Unsigned `UnityFramework.framework` build against the iPhoneOS SDK.
8. Copy of the framework to `iOSApp/GeneratedFrameworks/`.
9. SwiftUI host Xcode project generation.
10. Unsigned SwiftUI host build against the iPhoneOS SDK.
11. Generation of `.stage-a1/STAGE_A1_VM_REPORT.txt`.

### A1-VM PASS

PASS means all of the following succeeded:

- `unity_export=PASS`
- `unityframework_unsigned_build=PASS`
- `swiftui_host_unsigned_build=PASS`
- `bridge_static_contract=PASS`
- `STAGE_A1_VM=PASS`

A1-VM PASS is sufficient to continue Stage B data/tooling development.

It is **not** permission to claim Stage A FINAL CLOSED, real-device stability, real Metal performance, thermal performance, or final iPhone compatibility.

---

## Stage A1-Device

A1-Device remains a deferred but mandatory real-iPhone acceptance gate.

If the VM can pass a physical iPhone through USB to Xcode, run:

```bash
./BuildScripts/stage_a1_device_preflight.sh
```

If no physical iPhone is visible, the script returns `STAGE_A1_DEVICE_PREFLIGHT=DEFERRED`. That is not a project failure; it means device acceptance must be completed later on hardware/USB passthrough that Xcode can access.

When a physical iPhone is available:

1. Open `iOSApp/University3D.xcodeproj`.
2. Select the correct Apple Development Team.
3. Choose the physical iPhone destination.
4. Build and run.
5. Confirm SwiftUI host launches normally.
6. Confirm UnityFramework loads.
7. Confirm `Bootstrap.unity` renders `TEST-01`.
8. Press **Bridge Test**.
9. Confirm Swift sends `focusObject(TEST-01)`.
10. Confirm Unity receives it and returns `objectSelected(TEST-01)`.
11. Confirm Swift displays the returned event.
12. Test background → foreground and full relaunch.

Only after those checks pass may Stage A1-Device be marked PASS.

---

## Closure rule

The project may continue into Stage B after **A1-VM PASS**, because CampusData/schema/validator/generator work does not require pretending that the VM is a real device.

However:

- Stage A FINAL CLOSED requires A1-Device PASS.
- The first vertical-slice milestone is not FINAL until it runs on a real iPhone.
- Stage P performance closure always requires real iPhone measurements.
- VM or Simulator results must never be used as substitutes for FPS, thermal, memory-pressure, or long-run device evidence.

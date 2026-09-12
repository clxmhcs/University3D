# Jiangcheng University / 江城大学 — University3D

Stage A engineering skeleton for the Jiangcheng University 3D campus app.

Frozen architecture:

- SwiftUI owns app/business UI.
- Unity URP owns the 3D world and simulation.
- CampusData is the single authoritative business-data source.
- Swift ↔ Unity communication uses permanent object IDs through CampusBridgeProtocol v1.
- Campus content will later stream in 250m × 250m chunks.
- No Unity-scene manual coordinate system is allowed to become a second source of truth.

Current source override baseline:
`PATCH-2026-09-12-R5`.

## Stage A acceptance

Stage A is complete only after a real iPhone can:

1. Launch the SwiftUI host app.
2. Load the Unity URP test scene.
3. Send a `focusObject(TEST-01)` bridge message from Swift to Unity.
4. Receive `objectSelected(TEST-01)` from Unity to Swift.
5. Leave and re-enter the Unity view without crashing.

The complete campus is deliberately NOT built in Stage A.

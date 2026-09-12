# Stage A Acceptance Contract

## Source baseline

Before changing campus data, read the highest-priority override source:

`江城大学——数据源统一更新、废止与覆盖说明（最高优先级补丁）`

Current patch version used by this scaffold:

`PATCH-2026-09-12-R5`

## Frozen architecture

- SwiftUI: app/business UI.
- Unity URP: 3D world/simulation.
- CampusData: single authoritative business-data source.
- CampusBridgeProtocol v1: structured JSON messages using permanent IDs.
- Bootstrap scene contains persistent systems only.
- Full campus content is not embedded in Bootstrap.
- Chunk baseline: 250m × 250m.
- Addressables is the later resource-loading core.

## Stage A real-device acceptance

PASS requires all of the following on a real iPhone:

1. SwiftUI host launches normally.
2. UnityFramework loads a URP test scene.
3. `Bootstrap.unity` is the first Unity scene.
4. A visible `TEST-01` cube is rendered.
5. Swift sends:
   `{"protocolVersion":1,"type":"focusObject","objectID":"TEST-01"}`
6. Unity receives the message and responds:
   `{"protocolVersion":1,"type":"objectSelected","objectID":"TEST-01"}`
7. Swift receives and displays the returned event.
8. Unity can be left/re-entered without crash.
9. No campus building coordinates are manually invented in the Unity scene.

Do not mark Stage A FINAL CLOSED before the real-iPhone bridge test passes.

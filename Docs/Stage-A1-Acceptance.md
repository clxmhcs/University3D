# Stage A1 — Toolchain and real-device bridge acceptance

## Source contract

Every campus-data operation continues to obey the highest-priority source override patch:

`PATCH-2026-09-12-R5`

Stage A1 does not import the full campus yet. Its job is to make the SwiftUI host and Unity iOS export reproducible.

## Pinned toolchain

- Unity 6.3 LTS: `6000.3.15f1`
- URP: `17.3.0`
- Addressables: `2.7.6`
- Input System: `1.17.0`
- iOS deployment target: `17.0`
- Unity build backend: IL2CPP
- Graphics API: Metal only
- Bundle ID baseline: `com.clxmhcs.University3D`

The Apple Development Team is intentionally NOT stored in Git because it is account-specific.

## Prepare on the Mac

Run from repository root:

```bash
./BuildScripts/stage_a1_prepare.sh
```

The script will:

1. Validate the pinned Unity editor path.
2. Configure the Unity project for iOS / Metal / IL2CPP / URP.
3. Generate `Bootstrap.unity` with `TEST-01`.
4. Export the Unity iOS project.
5. Build `UnityFramework.framework` without code signing.
6. Copy it into the git-ignored `iOSApp/GeneratedFrameworks/` directory.
7. Generate the SwiftUI Xcode project with XcodeGen.
8. Run the Stage A1 static validator.

## Real-iPhone PASS conditions

Open `iOSApp/University3D.xcodeproj` in Xcode, select the user's Development Team, connect a real iPhone, then run.

PASS requires all of the following:

1. SwiftUI host launches normally.
2. UnityFramework is embedded and loads.
3. `Bootstrap.unity` renders `TEST-01`.
4. Pressing **Bridge Test** sends `focusObject(TEST-01)`.
5. Unity receives the message.
6. Unity sends `objectSelected(TEST-01)` back to Swift.
7. Swift displays the returned event.
8. App background/foreground and relaunch do not crash.
9. No real campus coordinate is manually invented in the Unity scene.

Do not mark Stage A1 FINAL CLOSED until these conditions pass on a real iPhone.

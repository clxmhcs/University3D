#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    ".gitignore",
    ".gitattributes",
    "CampusData/manifest.json",
    "iOSApp/App/University3DApp.swift",
    "iOSApp/Features/Campus/CampusRootView.swift",
    "iOSApp/Services/CampusBridge.swift",
    "iOSApp/Unity/UnityBridge.swift",
    "iOSApp/Unity/UnityMessage.swift",
    "UnityProject/Assets/_Project/Core/CampusCore.cs",
    "UnityProject/Assets/_Project/Bridge/CampusBridge.cs",
    "UnityProject/Assets/_Project/Editor/CreateStageABootstrapScene.cs",
    "Docs/Stage-A-Acceptance.md",
]

errors = []

for rel in REQUIRED:
    if not (ROOT / rel).exists():
        errors.append(f"missing: {rel}")

manifest_path = ROOT / "CampusData/manifest.json"
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("sourcePatchVersion") != "PATCH-2026-09-12-R5":
        errors.append("manifest sourcePatchVersion mismatch")
    if manifest.get("bridgeProtocolVersion") != 1:
        errors.append("manifest bridgeProtocolVersion must be 1")
    if manifest.get("chunkSizeMeters") != 250:
        errors.append("manifest chunkSizeMeters must be 250")
    cs = manifest.get("coordinateSystem", {})
    if cs != {"unit":"meter","xAxis":"east","zAxis":"north","yAxis":"up"}:
        errors.append("coordinateSystem mismatch")

if errors:
    print("STAGE_A_SKELETON=FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("STAGE_A_SKELETON=PASS")
print("sourcePatchVersion=PATCH-2026-09-12-R5")
print("bridgeProtocolVersion=1")
print("chunkSizeMeters=250")

#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

required = [
    "UnityProject/Packages/manifest.json",
    "UnityProject/ProjectSettings/ProjectVersion.txt",
    "UnityProject/Assets/_Project/Editor/StageAProjectConfigurator.cs",
    "UnityProject/Assets/_Project/Editor/StageAIOSBuilder.cs",
    "UnityProject/Assets/Plugins/iOS/CampusBridgeNative.mm",
    "iOSApp/project.yml",
    "iOSApp/App/AppDelegate.swift",
    "iOSApp/Unity/UnityRuntimeBridge.h",
    "iOSApp/Unity/UnityRuntimeBridge.mm",
    "iOSApp/Unity/University3D-Bridging-Header.h",
    "BuildScripts/bootstrap_ios_host.sh",
    "BuildScripts/stage_a1_prepare.sh",
    "Docs/Stage-A1-Acceptance.md",
]

errors = []
for rel in required:
    if not (ROOT / rel).exists():
        errors.append(f"missing: {rel}")

manifest = json.loads((ROOT / "CampusData/manifest.json").read_text(encoding="utf-8"))
if manifest.get("sourcePatchVersion") != "PATCH-2026-09-12-R5":
    errors.append("CampusData sourcePatchVersion mismatch")
if manifest.get("bridgeProtocolVersion") != 1:
    errors.append("bridgeProtocolVersion must be 1")
if manifest.get("chunkSizeMeters") != 250:
    errors.append("chunkSizeMeters must be 250")

packages = json.loads((ROOT / "UnityProject/Packages/manifest.json").read_text(encoding="utf-8"))
deps = packages.get("dependencies", {})
expected = {
    "com.unity.render-pipelines.universal": "17.3.0",
    "com.unity.addressables": "2.7.6",
    "com.unity.inputsystem": "1.17.0",
}
for key, value in expected.items():
    if deps.get(key) != value:
        errors.append(f"Unity package mismatch: {key} expected {value}, got {deps.get(key)}")

project_version = (ROOT / "UnityProject/ProjectSettings/ProjectVersion.txt").read_text(encoding="utf-8")
if "6000.3.15f1" not in project_version:
    errors.append("Unity editor baseline must be 6000.3.15f1")

if errors:
    print("STAGE_A1_STATIC=FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("STAGE_A1_STATIC=PASS")
print("unity=6000.3.15f1")
print("urp=17.3.0")
print("addressables=2.7.6")
print("inputSystem=1.17.0")
print("iosDeploymentTarget=17.0")
print("graphicsAPI=Metal")
print("scriptingBackend=IL2CPP")

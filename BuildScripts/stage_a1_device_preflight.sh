#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORT="$ROOT/.stage-a1/STAGE_A1_DEVICE_PREFLIGHT.txt"
mkdir -p "$ROOT/.stage-a1"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "STAGE_A1_DEVICE_PREFLIGHT=FAIL"
  echo "reason=macOS required"
  exit 2
fi

if ! command -v xcrun >/dev/null 2>&1; then
  echo "STAGE_A1_DEVICE_PREFLIGHT=FAIL"
  echo "reason=xcrun not found"
  exit 3
fi

DEVICES="$(xcrun xctrace list devices 2>/dev/null || true)"
PHYSICAL="$(printf '%s\n' "$DEVICES" | grep -E 'iPhone.*\([0-9A-Fa-f-]{8,}\)' | grep -v 'Simulator' || true)"

{
  echo "stage=Stage A1-Device preflight"
  echo "timestamp=$(date '+%Y-%m-%dT%H:%M:%S%z')"
  echo "sourcePatchVersion=PATCH-2026-09-12-R5"
  "$ROOT/BuildScripts/detect_macos_environment.sh"
  echo "physical_iPhone_detected=$([[ -n "$PHYSICAL" ]] && echo yes || echo no)"
  if [[ -n "$PHYSICAL" ]]; then
    echo "devices_begin"
    printf '%s\n' "$PHYSICAL"
    echo "devices_end"
  fi
} > "$REPORT"

cat "$REPORT"

if [[ -z "$PHYSICAL" ]]; then
  echo "STAGE_A1_DEVICE_PREFLIGHT=DEFERRED"
  echo "reason=no physical iPhone visible to Xcode; this is expected when VM USB passthrough is unavailable"
  exit 4
fi

echo "STAGE_A1_DEVICE_PREFLIGHT=READY"
echo "NEXT=Open iOSApp/University3D.xcodeproj, select Apple Development Team, run on the attached iPhone, and verify the bridge round-trip."

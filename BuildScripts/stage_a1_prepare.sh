#!/bin/bash
set -euo pipefail

MODE="${STAGE_A1_MODE:-vm}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

case "$MODE" in
  vm)
    exec "$ROOT/BuildScripts/stage_a1_vm_prepare.sh"
    ;;
  device)
    "$ROOT/BuildScripts/stage_a1_vm_prepare.sh"
    exec "$ROOT/BuildScripts/stage_a1_device_preflight.sh"
    ;;
  *)
    echo "ERROR: unsupported STAGE_A1_MODE=$MODE (expected vm or device)"
    exit 64
    ;;
esac

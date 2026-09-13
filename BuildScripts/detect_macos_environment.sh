#!/bin/bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "environment=non-macOS"
  exit 0
fi

VIRTUALIZED="unknown"
if sysctl -n kern.hv_vmm_present >/dev/null 2>&1; then
  if [[ "$(sysctl -n kern.hv_vmm_present 2>/dev/null || true)" == "1" ]]; then
    VIRTUALIZED="yes"
  else
    VIRTUALIZED="no"
  fi
fi

MODEL="$(system_profiler SPHardwareDataType 2>/dev/null | awk -F': ' '/Model Name/ {print $2; exit}')"
CHIP="$(system_profiler SPHardwareDataType 2>/dev/null | awk -F': ' '/Chip/ {print $2; exit}')"
OS_VERSION="$(sw_vers -productVersion 2>/dev/null || true)"
ARCH="$(uname -m)"

echo "environment=macOS"
echo "virtualized=$VIRTUALIZED"
echo "os=$OS_VERSION"
echo "arch=$ARCH"
echo "model=${MODEL:-unknown}"
echo "chip=${CHIP:-unknown}"

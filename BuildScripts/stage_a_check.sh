#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 Tools/validate_stage_a.py

echo "STAGE_A_STATIC_CHECK=PASS"
echo "NEXT=Create URP Unity project + Xcode SwiftUI host, then run real-iPhone bridge acceptance."

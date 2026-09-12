#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IOS_DIR="$ROOT/iOSApp"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "ERROR: iOS host generation requires macOS."
  exit 2
fi

if ! command -v xcodegen >/dev/null 2>&1; then
  echo "ERROR: XcodeGen is required. Install it with: brew install xcodegen"
  exit 3
fi

cd "$IOS_DIR"
xcodegen generate --spec project.yml

echo "IOS_HOST_PROJECT=PASS"
echo "project=$IOS_DIR/University3D.xcodeproj"

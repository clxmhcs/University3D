#!/bin/bash
set -euo pipefail

UNITY_VERSION="${UNITY_VERSION:-6000.3.15f1}"
UNITY_CHANGESET="${UNITY_CHANGESET:-c1aa84e375f6}"
ARCH="$(uname -m)"
CACHE_DIR="${HOME}/Library/Caches/University3D/Unity/${UNITY_VERSION}"
EDITOR_EXPECTED="/Applications/Unity/Hub/Editor/${UNITY_VERSION}/Unity.app/Contents/MacOS/Unity"

find_matching_editor() {
  local candidate version
  if [[ -x "$EDITOR_EXPECTED" ]]; then
    echo "$EDITOR_EXPECTED"
    return 0
  fi

  while IFS= read -r candidate; do
    [[ -x "$candidate" ]] || continue
    version="$($candidate -version 2>/dev/null | tail -n 1 || true)"
    if [[ "$version" == *"$UNITY_VERSION"* ]]; then
      echo "$candidate"
      return 0
    fi
  done < <(find /Applications -type f -path '*/Unity.app/Contents/MacOS/Unity' 2>/dev/null)

  return 1
}

case "$ARCH" in
  x86_64)
    EDITOR_PKG_URL="https://download.unity3d.com/download_unity/${UNITY_CHANGESET}/MacEditorInstaller/Unity-${UNITY_VERSION}.pkg"
    ;;
  arm64)
    EDITOR_PKG_URL="https://download.unity3d.com/download_unity/${UNITY_CHANGESET}/MacEditorInstallerArm64/Unity-${UNITY_VERSION}.pkg"
    ;;
  *)
    echo "UNITY_BOOTSTRAP=FAIL"
    echo "reason=unsupported macOS architecture: $ARCH"
    exit 2
    ;;
esac

IOS_PKG_URL="https://download.unity3d.com/download_unity/${UNITY_CHANGESET}/MacEditorTargetInstaller/UnitySetup-iOS-Support-for-Editor-${UNITY_VERSION}.pkg"
EDITOR_PKG="$CACHE_DIR/Unity-${UNITY_VERSION}-${ARCH}.pkg"
IOS_PKG="$CACHE_DIR/UnitySetup-iOS-Support-for-Editor-${UNITY_VERSION}.pkg"

if EXISTING="$(find_matching_editor)"; then
  echo "UNITY_BOOTSTRAP=PASS"
  echo "unity_editor=$EXISTING"
  "$EXISTING" -version || true
  exit 0
fi

command -v curl >/dev/null 2>&1 || { echo "UNITY_BOOTSTRAP=FAIL"; echo "reason=curl not found"; exit 3; }
command -v sudo >/dev/null 2>&1 || { echo "UNITY_BOOTSTRAP=FAIL"; echo "reason=sudo not found"; exit 3; }
[[ -x /usr/sbin/installer ]] || { echo "UNITY_BOOTSTRAP=FAIL"; echo "reason=macOS installer tool not found"; exit 3; }

mkdir -p "$CACHE_DIR"

download_pkg() {
  local url="$1"
  local dst="$2"
  local label="$3"

  echo "===== Downloading $label ====="
  echo "url=$url"
  echo "dst=$dst"

  /usr/bin/curl \
    --fail \
    --location \
    --http1.1 \
    -4 \
    --retry 8 \
    --retry-delay 5 \
    --retry-all-errors \
    --connect-timeout 45 \
    --speed-limit 1024 \
    --speed-time 120 \
    --continue-at - \
    --output "$dst" \
    "$url"
}

if [[ ! -s "$EDITOR_PKG" ]]; then
  download_pkg "$EDITOR_PKG_URL" "$EDITOR_PKG" "Unity Editor ${UNITY_VERSION} (${ARCH})"
else
  echo "Reusing cached editor package: $EDITOR_PKG"
fi

if [[ ! -s "$IOS_PKG" ]]; then
  download_pkg "$IOS_PKG_URL" "$IOS_PKG" "Unity iOS Build Support ${UNITY_VERSION}"
else
  echo "Reusing cached iOS support package: $IOS_PKG"
fi

echo "===== Installing Unity Editor ====="
echo "A macOS administrator password may be requested by sudo."
sudo /usr/sbin/installer -pkg "$EDITOR_PKG" -target /

echo "===== Installing Unity iOS Build Support ====="
sudo /usr/sbin/installer -pkg "$IOS_PKG" -target /

if FOUND="$(find_matching_editor)"; then
  echo "UNITY_BOOTSTRAP=PASS"
  echo "unity_editor=$FOUND"
  "$FOUND" -version || true
  exit 0
fi

echo "UNITY_BOOTSTRAP=FAIL"
echo "reason=Unity packages installed, but ${UNITY_VERSION} editor executable was not found under /Applications"
echo "expected=$EDITOR_EXPECTED"
exit 4

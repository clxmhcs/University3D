#!/bin/bash
set -euo pipefail

UNITY_VERSION="${UNITY_VERSION:-6000.3.15f1}"
UNITY_CHANGESET="${UNITY_CHANGESET:-c1aa84e375f6}"
ARCH="$(uname -m)"
CACHE_DIR="${HOME}/Library/Caches/University3D/Unity/${UNITY_VERSION}"
EDITOR_EXPECTED="/Applications/Unity/Hub/Editor/${UNITY_VERSION}/Unity.app/Contents/MacOS/Unity"
RELEASE_PAGE="https://unity.com/releases/editor/whats-new/${UNITY_VERSION}"

# These paths are the exact links published by Unity's release page for this
# pinned build. In some VM networks curl receives a synthetic/edge 404 even
# though the same objects are available through a normal browser. Keep network
# retries, but also support verified packages manually placed in ~/Downloads.
UNITY_BASE_URLS=(
  "https://download.unity3d.com/download_unity"
  "https://beta.unity3d.com/download"
  "https://netstorage.unity3d.com/unity"
)

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
    EDITOR_REL="MacEditorInstaller/Unity-${UNITY_VERSION}.pkg"
    ;;
  arm64)
    EDITOR_REL="MacEditorInstallerArm64/Unity-${UNITY_VERSION}.pkg"
    ;;
  *)
    echo "UNITY_BOOTSTRAP=FAIL"
    echo "reason=unsupported macOS architecture: $ARCH"
    exit 2
    ;;
esac

IOS_REL="MacEditorTargetInstaller/UnitySetup-iOS-Support-for-Editor-${UNITY_VERSION}.pkg"
EDITOR_PKG="$CACHE_DIR/Unity-${UNITY_VERSION}-${ARCH}.pkg"
IOS_PKG="$CACHE_DIR/UnitySetup-iOS-Support-for-Editor-${UNITY_VERSION}.pkg"
OFFICIAL_EDITOR_URL="https://download.unity3d.com/download_unity/${UNITY_CHANGESET}/${EDITOR_REL}"
OFFICIAL_IOS_URL="https://download.unity3d.com/download_unity/${UNITY_CHANGESET}/${IOS_REL}"

if EXISTING="$(find_matching_editor)"; then
  echo "UNITY_BOOTSTRAP=PASS"
  echo "unity_editor=$EXISTING"
  "$EXISTING" -version || true
  exit 0
fi

command -v curl >/dev/null 2>&1 || { echo "UNITY_BOOTSTRAP=FAIL"; echo "reason=curl not found"; exit 3; }
command -v sudo >/dev/null 2>&1 || { echo "UNITY_BOOTSTRAP=FAIL"; echo "reason=sudo not found"; exit 3; }
[[ -x /usr/sbin/installer ]] || { echo "UNITY_BOOTSTRAP=FAIL"; echo "reason=macOS installer tool not found"; exit 3; }
[[ -x /usr/sbin/pkgutil ]] || { echo "UNITY_BOOTSTRAP=FAIL"; echo "reason=macOS pkgutil tool not found"; exit 3; }

mkdir -p "$CACHE_DIR"

package_is_valid() {
  local pkg="$1"
  [[ -s "$pkg" ]] || return 1
  /usr/sbin/pkgutil --check-signature "$pkg" >/dev/null 2>&1
}

adopt_manual_pkg() {
  local dst="$1"
  local exact_name="$2"
  local explicit_path="$3"
  local candidate=""

  if [[ -n "$explicit_path" && -f "$explicit_path" ]]; then
    candidate="$explicit_path"
  elif [[ -f "$HOME/Downloads/$exact_name" ]]; then
    candidate="$HOME/Downloads/$exact_name"
  else
    candidate="$(find "$HOME/Downloads" -maxdepth 1 -type f -name "${exact_name%.pkg}*.pkg" -print 2>/dev/null | head -n 1 || true)"
  fi

  [[ -n "$candidate" ]] || return 1

  echo "Found manual package candidate: $candidate"
  if ! package_is_valid "$candidate"; then
    echo "WARNING: manual package signature validation failed: $candidate"
    return 1
  fi

  cp "$candidate" "$dst"
  echo "MANUAL_PACKAGE_VERIFIED=PASS"
  echo "source=$candidate"
  echo "cached=$dst"
  return 0
}

curl_common() {
  local url="$1"
  local dst="$2"
  shift 2

  /usr/bin/curl \
    --fail \
    --location \
    --retry 2 \
    --retry-delay 5 \
    --connect-timeout 45 \
    --speed-limit 1024 \
    --speed-time 120 \
    --continue-at - \
    --output "$dst" \
    "$@" \
    "$url"
}

curl_once() {
  local url="$1"
  local dst="$2"
  local transport="$3"

  echo "transport=$transport"

  case "$transport" in
    auto)
      curl_common "$url" "$dst"
      ;;
    http1)
      curl_common "$url" "$dst" --http1.1
      ;;
    ipv4-http1)
      curl_common "$url" "$dst" --http1.1 -4
      ;;
    ipv6-http1)
      curl_common "$url" "$dst" --http1.1 -6
      ;;
    *)
      echo "WARNING: unsupported transport mode: $transport"
      return 64
      ;;
  esac
}

download_pkg() {
  local rel="$1"
  local dst="$2"
  local label="$3"
  local exact_name="$4"
  local explicit_path="$5"
  local base url transport

  echo "===== Preparing $label ====="
  echo "changeset=$UNITY_CHANGESET"
  echo "dst=$dst"

  if package_is_valid "$dst"; then
    echo "Reusing verified cached package: $dst"
    return 0
  fi

  if adopt_manual_pkg "$dst" "$exact_name" "$explicit_path"; then
    return 0
  fi

  if [[ -e "$dst" ]]; then
    echo "Existing cache is incomplete or invalid; resume will be attempted."
    echo "cachedBytes=$(stat -f%z "$dst" 2>/dev/null || echo 0)"
  fi

  for base in "${UNITY_BASE_URLS[@]}"; do
    url="${base}/${UNITY_CHANGESET}/${rel}"
    echo "----- CDN candidate -----"
    echo "url=$url"

    for transport in auto http1 ipv4-http1 ipv6-http1; do
      if curl_once "$url" "$dst" "$transport"; then
        if package_is_valid "$dst"; then
          echo "DOWNLOAD_VERIFIED=PASS"
          echo "source=$url"
          echo "transport=$transport"
          return 0
        fi

        echo "WARNING: download completed but package signature validation failed; discarding cache."
        rm -f "$dst"
      else
        echo "WARNING: download attempt failed for $url ($transport)"
      fi
    done
  done

  # One last manual check in case the user downloaded the package while this
  # script was cycling through network routes.
  if adopt_manual_pkg "$dst" "$exact_name" "$explicit_path"; then
    return 0
  fi

  echo "UNITY_DOWNLOAD=FAIL"
  echo "label=$label"
  echo "relativePath=$rel"
  echo "releasePage=$RELEASE_PAGE"
  echo "reason=VM network could not fetch the official Unity package and no verified manual package was found"
  return 1
}

download_pkg "$EDITOR_REL" "$EDITOR_PKG" "Unity Editor ${UNITY_VERSION} (${ARCH})" "Unity-${UNITY_VERSION}.pkg" "${UNITY_EDITOR_PKG:-}" || {
  echo "UNITY_BOOTSTRAP=FAIL"
  echo "reason=unable to obtain Unity Editor ${UNITY_VERSION}"
  echo "officialEditorURL=$OFFICIAL_EDITOR_URL"
  echo "manualFallback=Download the macOS package from the Unity release page and place it in ~/Downloads/Unity-${UNITY_VERSION}.pkg"
  exit 4
}

download_pkg "$IOS_REL" "$IOS_PKG" "Unity iOS Build Support ${UNITY_VERSION}" "UnitySetup-iOS-Support-for-Editor-${UNITY_VERSION}.pkg" "${UNITY_IOS_PKG:-}" || {
  echo "UNITY_BOOTSTRAP=FAIL"
  echo "reason=unable to obtain Unity iOS Build Support ${UNITY_VERSION}"
  echo "officialIOSURL=$OFFICIAL_IOS_URL"
  echo "manualFallback=Download iOS Build Support from the Unity release page and place it in ~/Downloads/UnitySetup-iOS-Support-for-Editor-${UNITY_VERSION}.pkg"
  exit 4
}

echo "===== Installing Unity Editor ====="
echo "A macOS administrator password may be requested by sudo."
sudo /usr/sbin/installer -pkg "$EDITOR_PKG" -target /

if ! INSTALLED_EDITOR="$(find_matching_editor)"; then
  echo "UNITY_BOOTSTRAP=FAIL"
  echo "reason=Unity Editor package installed, but ${UNITY_VERSION} executable was not found under /Applications"
  echo "expected=$EDITOR_EXPECTED"
  exit 5
fi

echo "unity_editor=$INSTALLED_EDITOR"
"$INSTALLED_EDITOR" -version || true

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
exit 6

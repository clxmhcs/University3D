#!/bin/bash
set -euo pipefail

UNITY_VERSION="${UNITY_VERSION:-6000.3.15f1}"
UNITY_CHANGESET="${UNITY_CHANGESET:-c1aa84e375f6}"
ARCH="$(uname -m)"
CACHE_DIR="${HOME}/Library/Caches/University3D/Unity/${UNITY_VERSION}"
EDITOR_EXPECTED="/Applications/Unity/Hub/Editor/${UNITY_VERSION}/Unity.app/Contents/MacOS/Unity"

# Unity's release page currently publishes download.unity3d.com links. Some VM/CDN
# routes can return an edge-specific 404 even when the object exists. Unity-owned
# beta/netstorage hosts use the same changeset-relative package layout, so we try
# them as transport fallbacks without changing the pinned editor build.
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

curl_once() {
  local url="$1"
  local dst="$2"
  local transport="$3"
  local -a transport_args=()

  case "$transport" in
    auto)
      transport_args=()
      ;;
    http1)
      transport_args=(--http1.1)
      ;;
    ipv4-http1)
      transport_args=(--http1.1 -4)
      ;;
    ipv6-http1)
      transport_args=(--http1.1 -6)
      ;;
    *)
      return 64
      ;;
  esac

  echo "transport=$transport"
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
    "${transport_args[@]}" \
    "$url"
}

download_pkg() {
  local rel="$1"
  local dst="$2"
  local label="$3"
  local base url transport

  echo "===== Downloading $label ====="
  echo "changeset=$UNITY_CHANGESET"
  echo "dst=$dst"

  if package_is_valid "$dst"; then
    echo "Reusing verified cached package: $dst"
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

  echo "UNITY_DOWNLOAD=FAIL"
  echo "label=$label"
  echo "relativePath=$rel"
  echo "releasePage=https://unity.com/releases/editor/whats-new/${UNITY_VERSION}"
  echo "reason=all Unity-owned CDN routes/transports failed"
  return 1
}

download_pkg "$EDITOR_REL" "$EDITOR_PKG" "Unity Editor ${UNITY_VERSION} (${ARCH})" || {
  echo "UNITY_BOOTSTRAP=FAIL"
  echo "reason=unable to download Unity Editor ${UNITY_VERSION} from Unity-owned CDN routes"
  exit 4
}

download_pkg "$IOS_REL" "$IOS_PKG" "Unity iOS Build Support ${UNITY_VERSION}" || {
  echo "UNITY_BOOTSTRAP=FAIL"
  echo "reason=unable to download Unity iOS Build Support ${UNITY_VERSION} from Unity-owned CDN routes"
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

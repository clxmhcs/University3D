#!/bin/bash
set -eo pipefail

XCODEGEN_VERSION="${XCODEGEN_VERSION:-2.46.0}"
INSTALL_DIR="${HOME}/.local/bin"
WORK_DIR="${TMPDIR:-/tmp}/University3D-XcodeGen-${XCODEGEN_VERSION}"
REPO_URL="https://github.com/yonaskolb/XcodeGen.git"

if command -v xcodegen >/dev/null 2>&1; then
  echo "XCODEGEN_BOOTSTRAP=PASS"
  echo "xcodegen=$(command -v xcodegen)"
  xcodegen --version || true
  exit 0
fi

command -v git >/dev/null 2>&1 || { echo "XCODEGEN_BOOTSTRAP=FAIL"; echo "reason=git not found"; exit 2; }
command -v swift >/dev/null 2>&1 || { echo "XCODEGEN_BOOTSTRAP=FAIL"; echo "reason=swift not found; Xcode command line tools are required"; exit 3; }

mkdir -p "$INSTALL_DIR"
rm -rf "$WORK_DIR"

echo "===== XcodeGen bootstrap without Homebrew ====="
echo "version=$XCODEGEN_VERSION"
echo "source=$REPO_URL"
echo "installDir=$INSTALL_DIR"

# The VM can reach github.com through git even when raw.githubusercontent.com
# has TLS/SSL handshake timeouts. Force IPv4 + HTTP/1.1 to avoid common
# virtualized-network HTTP/2/IPv6 failures.
if ! GIT_CURL_VERBOSE=0 git -c http.version=HTTP/1.1 clone \
  -c http.lowSpeedLimit=1 \
  -c http.lowSpeedTime=60 \
  --depth 1 \
  --branch "$XCODEGEN_VERSION" \
  "$REPO_URL" \
  "$WORK_DIR"; then
  echo "XCODEGEN_BOOTSTRAP=FAIL"
  echo "reason=unable to clone XcodeGen from github.com"
  echo "hint=git pull for University3D works, so retrying later may be enough; raw.githubusercontent.com is not required by this path"
  exit 4
fi

cd "$WORK_DIR"

swift build -c release --product xcodegen
BIN_DIR="$(swift build -c release --show-bin-path)"

if [[ ! -x "$BIN_DIR/xcodegen" ]]; then
  echo "XCODEGEN_BOOTSTRAP=FAIL"
  echo "reason=Swift build completed but xcodegen binary was not found at $BIN_DIR/xcodegen"
  exit 5
fi

cp "$BIN_DIR/xcodegen" "$INSTALL_DIR/xcodegen"
chmod +x "$INSTALL_DIR/xcodegen"

PROFILE="$HOME/.zprofile"
touch "$PROFILE"
if ! grep -Fq 'export PATH="$HOME/.local/bin:$PATH"' "$PROFILE"; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$PROFILE"
fi

export PATH="$INSTALL_DIR:$PATH"

if ! command -v xcodegen >/dev/null 2>&1; then
  echo "XCODEGEN_BOOTSTRAP=FAIL"
  echo "reason=xcodegen installed but not discoverable in PATH"
  exit 6
fi

echo "XCODEGEN_BOOTSTRAP=PASS"
echo "xcodegen=$(command -v xcodegen)"
xcodegen --version

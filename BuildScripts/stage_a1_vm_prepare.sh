#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UNITY_VERSION="6000.3.15f1"
UNITY_EDITOR_DEFAULT="/Applications/Unity/Hub/Editor/${UNITY_VERSION}/Unity.app/Contents/MacOS/Unity"
UNITY_EDITOR="${UNITY_EDITOR:-$UNITY_EDITOR_DEFAULT}"
UNITY_PROJECT="$ROOT/UnityProject"
UNITY_EXPORT="$UNITY_PROJECT/Builds/iOS"
UNITY_DERIVED="$ROOT/.stage-a1/UnityDerivedData"
HOST_DERIVED="$ROOT/.stage-a1/HostDerivedData"
FRAMEWORK_DST="$ROOT/iOSApp/GeneratedFrameworks"
REPORT="$ROOT/.stage-a1/STAGE_A1_VM_REPORT.txt"

fail() {
  echo "STAGE_A1_VM=FAIL"
  echo "reason=$1"
  exit "${2:-1}"
}

[[ "$(uname -s)" == "Darwin" ]] || fail "macOS is required" 2
command -v xcodebuild >/dev/null 2>&1 || fail "xcodebuild not found" 3
command -v python3 >/dev/null 2>&1 || fail "python3 not found" 3
command -v git >/dev/null 2>&1 || fail "git not found" 3
command -v swift >/dev/null 2>&1 || fail "swift not found; Xcode command line tools are required" 3

# Homebrew is optional. VM environments can fail to reach raw.githubusercontent.com
# even while normal GitHub git traffic works. Bootstrap a pinned XcodeGen directly
# from its official GitHub repository when no xcodegen binary is present.
export PATH="$HOME/.local/bin:$PATH"
if ! command -v xcodegen >/dev/null 2>&1; then
  chmod +x "$ROOT/BuildScripts/bootstrap_xcodegen.sh" 2>/dev/null || true
  "$ROOT/BuildScripts/bootstrap_xcodegen.sh" || fail "XcodeGen bootstrap failed" 3
  export PATH="$HOME/.local/bin:$PATH"
fi
command -v xcodegen >/dev/null 2>&1 || fail "xcodegen not found after bootstrap" 3

[[ -x "$UNITY_EDITOR" ]] || fail "Unity ${UNITY_VERSION} not found at $UNITY_EDITOR; set UNITY_EDITOR to override" 4

mkdir -p "$ROOT/.stage-a1" "$FRAMEWORK_DST"

{
  echo "stage=Stage A1-VM"
  echo "timestamp=$(date '+%Y-%m-%dT%H:%M:%S%z')"
  echo "sourcePatchVersion=PATCH-2026-09-12-R5"
  echo "unity=$UNITY_VERSION"
  echo "mode=vm"
  echo "xcodegen=$(command -v xcodegen)"
  xcodegen --version || true
  "$ROOT/BuildScripts/detect_macos_environment.sh"
  xcodebuild -version
} > "$REPORT"

python3 "$ROOT/Tools/validate_stage_a1.py"

"$UNITY_EDITOR" -batchmode -nographics -quit -projectPath "$UNITY_PROJECT" \
  -executeMethod JiangchengUniversity.EditorTools.StageAProjectConfigurator.Configure \
  -logFile "$ROOT/.stage-a1/unity-configure.log"

"$UNITY_EDITOR" -batchmode -nographics -quit -projectPath "$UNITY_PROJECT" \
  -executeMethod JiangchengUniversity.EditorTools.CreateStageABootstrapScene.Create \
  -logFile "$ROOT/.stage-a1/unity-bootstrap.log"

"$UNITY_EDITOR" -batchmode -nographics -quit -projectPath "$UNITY_PROJECT" \
  -executeMethod JiangchengUniversity.EditorTools.StageAIOSBuilder.Build \
  -logFile "$ROOT/.stage-a1/unity-ios-export.log"

xcodebuild \
  -project "$UNITY_EXPORT/Unity-iPhone.xcodeproj" \
  -scheme UnityFramework \
  -configuration Debug \
  -sdk iphoneos \
  -derivedDataPath "$UNITY_DERIVED" \
  CODE_SIGNING_ALLOWED=NO \
  CODE_SIGNING_REQUIRED=NO \
  build | tee "$ROOT/.stage-a1/unityframework-xcodebuild.log"

FRAMEWORK_SRC="$(find "$UNITY_DERIVED/Build/Products" -type d -name UnityFramework.framework | head -n 1)"
[[ -n "$FRAMEWORK_SRC" ]] || fail "UnityFramework.framework was not produced" 5

rm -rf "$FRAMEWORK_DST/UnityFramework.framework"
cp -R "$FRAMEWORK_SRC" "$FRAMEWORK_DST/UnityFramework.framework"

"$ROOT/BuildScripts/bootstrap_ios_host.sh"

xcodebuild \
  -project "$ROOT/iOSApp/University3D.xcodeproj" \
  -scheme University3D \
  -configuration Debug \
  -sdk iphoneos \
  -derivedDataPath "$HOST_DERIVED" \
  CODE_SIGNING_ALLOWED=NO \
  CODE_SIGNING_REQUIRED=NO \
  build | tee "$ROOT/.stage-a1/host-xcodebuild.log"

python3 "$ROOT/Tools/validate_stage_a1.py"

{
  echo "unity_export=PASS"
  echo "unityframework_unsigned_build=PASS"
  echo "swiftui_host_unsigned_build=PASS"
  echo "bridge_static_contract=PASS"
  echo "device_acceptance=DEFERRED"
  echo "STAGE_A1_VM=PASS"
} >> "$REPORT"

cat "$REPORT"
echo "NEXT=Stage B may proceed, but Stage A FINAL CLOSED remains blocked until Stage A1-Device passes on a real iPhone."

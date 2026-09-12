#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UNITY_VERSION="6000.3.15f1"
UNITY_EDITOR_DEFAULT="/Applications/Unity/Hub/Editor/${UNITY_VERSION}/Unity.app/Contents/MacOS/Unity"
UNITY_EDITOR="${UNITY_EDITOR:-$UNITY_EDITOR_DEFAULT}"
UNITY_PROJECT="$ROOT/UnityProject"
UNITY_EXPORT="$UNITY_PROJECT/Builds/iOS"
UNITY_DERIVED="$ROOT/.stage-a1/UnityDerivedData"
FRAMEWORK_DST="$ROOT/iOSApp/GeneratedFrameworks"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "ERROR: Stage A1 preparation requires macOS."
  exit 2
fi

if [[ ! -x "$UNITY_EDITOR" ]]; then
  echo "ERROR: Unity ${UNITY_VERSION} not found at: $UNITY_EDITOR"
  echo "Set UNITY_EDITOR=/path/to/Unity to override."
  exit 3
fi

mkdir -p "$ROOT/.stage-a1" "$FRAMEWORK_DST"

"$UNITY_EDITOR" -batchmode -quit -projectPath "$UNITY_PROJECT" \
  -executeMethod JiangchengUniversity.EditorTools.StageAProjectConfigurator.Configure \
  -logFile "$ROOT/.stage-a1/unity-configure.log"

"$UNITY_EDITOR" -batchmode -quit -projectPath "$UNITY_PROJECT" \
  -executeMethod JiangchengUniversity.EditorTools.CreateStageABootstrapScene.Create \
  -logFile "$ROOT/.stage-a1/unity-bootstrap.log"

"$UNITY_EDITOR" -batchmode -quit -projectPath "$UNITY_PROJECT" \
  -executeMethod JiangchengUniversity.EditorTools.StageAIOSBuilder.Build \
  -logFile "$ROOT/.stage-a1/unity-ios-export.log"

xcodebuild \
  -project "$UNITY_EXPORT/Unity-iPhone.xcodeproj" \
  -scheme UnityFramework \
  -configuration Debug \
  -sdk iphoneos \
  -derivedDataPath "$UNITY_DERIVED" \
  CODE_SIGNING_ALLOWED=NO \
  build

FRAMEWORK_SRC="$(find "$UNITY_DERIVED/Build/Products" -type d -name UnityFramework.framework | head -n 1)"
if [[ -z "$FRAMEWORK_SRC" ]]; then
  echo "ERROR: UnityFramework.framework was not produced."
  exit 4
fi

rm -rf "$FRAMEWORK_DST/UnityFramework.framework"
cp -R "$FRAMEWORK_SRC" "$FRAMEWORK_DST/UnityFramework.framework"

"$ROOT/BuildScripts/bootstrap_ios_host.sh"
python3 "$ROOT/Tools/validate_stage_a1.py"

echo "STAGE_A1_PREPARE=PASS"
echo "NEXT=Open iOSApp/University3D.xcodeproj, select your Apple Development Team, connect iPhone, and run the Stage A1 bridge acceptance."

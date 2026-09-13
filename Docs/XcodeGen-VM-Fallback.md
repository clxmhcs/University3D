# XcodeGen VM fallback

The Stage A1 VM path does not require Homebrew.

If `xcodegen` is missing, `BuildScripts/stage_a1_vm_prepare.sh` invokes `BuildScripts/bootstrap_xcodegen.sh`, which builds XcodeGen `2.46.0` from the official `yonaskolb/XcodeGen` GitHub repository using Swift Package Manager and installs it to `~/.local/bin/xcodegen`.

This specifically avoids reliance on `raw.githubusercontent.com`, which can fail TLS handshakes in some virtual-machine network configurations even when normal Git operations against `github.com` succeed.

# Stage A1-VM Runbook

The current development machine is a macOS virtual machine. Use this runbook before asking the VM to behave like a physical iPhone.

## One command

From the repository root:

```bash
./BuildScripts/stage_a1_prepare.sh
```

Expected final marker:

```text
STAGE_A1_VM=PASS
```

The full local report is written to:

```text
.stage-a1/STAGE_A1_VM_REPORT.txt
```

## What PASS proves

- Unity project can be configured headlessly.
- `Bootstrap.unity` can be generated.
- Unity can export an iOS project.
- `UnityFramework.framework` can compile unsigned against the iPhoneOS SDK.
- The SwiftUI host can compile unsigned against the iPhoneOS SDK.
- The Stage A1 bridge source contract is present.

## What PASS does not prove

- USB passthrough works.
- An iPhone can be signed/deployed from the VM.
- Unity renders correctly on a real iPhone.
- Real-device Metal performance is acceptable.
- Thermal/memory/long-run targets pass.

Those remain Stage A1-Device / Stage P responsibilities.

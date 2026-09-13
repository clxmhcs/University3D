#!/usr/bin/env python3
"""Package the frozen Step-7 masterplan into canonical Step-8 release artifacts.

Step 8 is packaging/audit only. It is intentionally forbidden from changing
map geometry, label text or layer content. Canonical files differ from Step 7
only in root release title/metadata strings.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "CampusData/svg/step8_release_policy_r6.json"
PATCH = "PATCH-2026-09-13-R6"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_policy() -> dict:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if policy.get("sourcePatchVersion") != PATCH:
        raise SystemExit("Step 8 release policy patch mismatch")
    return policy


def release_transform(text: str, profile: str, release_version: str) -> str:
    if "step=7;" not in text or "generator=Tools/generate_svg_step7.py;" not in text:
        raise ValueError(f"{profile}: Step-7 lineage metadata not found")
    release_name = "Engineering Release" if profile == "engineering" else "Presentation Release"
    text = text.replace(
        "江城大学总平面 R6 — Step 7",
        f"江城大学总平面 R6 — {release_name}",
        1,
    )
    text = text.replace(
        "generator=Tools/generate_svg_step7.py;",
        f"generator=Tools/release_svg_step8.py; releaseVersion={release_version}; lineageGenerator=Tools/generate_svg_step7.py;",
        1,
    )
    text = text.replace(
        "step=7; deliveryLayerSchema=step7;",
        "lineageStep=7; release=true; deliveryLayerSchema=step7;",
        1,
    )
    return text


def write_release_svg(source: Path, target: Path, profile: str, release_version: str) -> None:
    text = source.read_text(encoding="utf-8")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(release_transform(text, profile, release_version), encoding="utf-8")
    print(f"WROTE {target.relative_to(ROOT)}")


def build_evidence(policy: dict) -> dict:
    evidence = {
        "schemaVersion": 1,
        "releaseVersion": policy["releaseVersion"],
        "sourcePatchVersion": policy["sourcePatchVersion"],
        "lineageStep": 7,
        "deterministic": True,
        "timestampOmittedByDesign": True,
        "canonicalFiles": {},
        "deterministicInputs": {},
    }
    for profile in ("engineering", "presentation"):
        source_rel = policy["sourceStep7"][profile]
        target_rel = policy["canonicalOutputs"][profile]
        source = ROOT / source_rel
        target = ROOT / target_rel
        evidence["canonicalFiles"][profile] = {
            "path": target_rel,
            "sha256": sha256_file(target),
            "sizeBytes": target.stat().st_size,
            "sourceStep7Path": source_rel,
            "sourceStep7Sha256": sha256_file(source),
            "contentRule": "Step7 content master; release title/metadata only",
        }
    for rel in policy["deterministicInputs"]:
        path = ROOT / rel
        if not path.exists():
            raise FileNotFoundError(rel)
        evidence["deterministicInputs"][rel] = sha256_file(path)
    return evidence


def write_evidence(policy: dict) -> None:
    evidence_rel = policy["canonicalOutputs"]["evidenceJson"]
    evidence_path = ROOT / evidence_rel
    evidence = build_evidence(policy)
    evidence_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    sha_rel = policy["canonicalOutputs"]["sha256Text"]
    sha_path = ROOT / sha_rel
    lines = [
        f"{sha256_file(ROOT / policy['canonicalOutputs']['engineering'])}  {policy['canonicalOutputs']['engineering']}",
        f"{sha256_file(ROOT / policy['canonicalOutputs']['presentation'])}  {policy['canonicalOutputs']['presentation']}",
        f"{sha256_file(evidence_path)}  {evidence_rel}",
    ]
    sha_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WROTE {evidence_path.relative_to(ROOT)}")
    print(f"WROTE {sha_path.relative_to(ROOT)}")


def main() -> None:
    policy = load_policy()
    for profile in ("engineering", "presentation"):
        source = ROOT / policy["sourceStep7"][profile]
        target = ROOT / policy["canonicalOutputs"][profile]
        write_release_svg(source, target, profile, policy["releaseVersion"])
    write_evidence(policy)


if __name__ == "__main__":
    main()

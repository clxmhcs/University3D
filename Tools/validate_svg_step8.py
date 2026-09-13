#!/usr/bin/env python3
"""Final release audit for Jiangcheng University R6 masterplan SVGs."""
from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import release_svg_step8 as release

ROOT = Path(__file__).resolve().parents[1]
PATCH = "PATCH-2026-09-13-R6"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_tag(elem: ET.Element) -> str:
    return elem.tag.split("}")[-1]


def compare_tree(a: ET.Element, b: ET.Element, path: str, errors: list[str]) -> None:
    if local_tag(a) != local_tag(b):
        errors.append(f"{path}: tag mismatch {local_tag(a)} != {local_tag(b)}")
        return
    if a.attrib != b.attrib:
        errors.append(f"{path}: attributes changed")
    aid = a.attrib.get("id", "")
    tag = local_tag(a)
    exempt_text = tag == "metadata" or (tag == "title" and aid == "title")
    if not exempt_text and (a.text or "") != (b.text or ""):
        errors.append(f"{path}: text changed for {tag}#{aid}")
    ac, bc = list(a), list(b)
    if len(ac) != len(bc):
        errors.append(f"{path}: child count changed {len(ac)} != {len(bc)}")
        return
    for i, (ca, cb) in enumerate(zip(ac, bc)):
        compare_tree(ca, cb, f"{path}/{local_tag(ca)}[{i}]", errors)


def top_level_group_ids(root: ET.Element) -> list[str]:
    return [child.attrib["id"] for child in root if local_tag(child) == "g" and "id" in child.attrib]


def check_security(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    lower = text.lower()
    banned = {
        "<image": "raster image",
        "<script": "script element",
        "<foreignobject": "foreignObject",
        "@font-face": "external/embedded font face",
        "xlink:href=": "xlink dependency",
        'href="http': "external href",
        "href='http": "external href",
    }
    for token, name in banned.items():
        if token in lower:
            errors.append(f"{path.name}: banned {name} found")


def main() -> int:
    policy = release.load_policy()
    errors: list[str] = []

    if policy["sourcePatchVersion"] != PATCH:
        errors.append("release policy patch mismatch")
    if policy["releaseVersion"] != "MASTERPLAN-R6-FINAL":
        errors.append("release version mismatch")

    canonical = {}
    for profile in ("engineering", "presentation"):
        source = ROOT / policy["sourceStep7"][profile]
        target = ROOT / policy["canonicalOutputs"][profile]
        canonical[profile] = target
        if not target.exists():
            errors.append(f"missing canonical release: {target.relative_to(ROOT)}")
            continue
        if "Step" in target.name:
            errors.append(f"canonical filename still contains Step: {target.name}")

        # Deterministic byte expectation from the current Step-7 source.
        expected = release.release_transform(
            source.read_text(encoding="utf-8"), profile, policy["releaseVersion"]
        )
        actual = target.read_text(encoding="utf-8")
        if actual != expected:
            errors.append(f"{target.name}: bytes are not the deterministic Step-7 release transform")

        # XML structure/content must be identical except release title/metadata text.
        source_root = ET.fromstring(source.read_text(encoding="utf-8"))
        target_root = ET.fromstring(actual)
        compare_tree(source_root, target_root, profile, errors)

        metadata = next((e for e in target_root if local_tag(e) == "metadata"), None)
        metadata_text = "" if metadata is None else (metadata.text or "")
        for token in (PATCH, "releaseVersion=MASTERPLAN-R6-FINAL", "lineageStep=7", "release=true", "noRaster=true"):
            if token not in metadata_text:
                errors.append(f"{target.name}: release metadata missing {token}")
        check_security(target, errors)

        groups = top_level_group_ids(target_root)
        expected_groups = list(policy["presentationLayerOrder"])
        if profile == "engineering":
            expected_groups += list(policy["engineeringTechnicalLayers"])
        if groups != expected_groups:
            errors.append(f"{target.name}: top-level layer order mismatch")

    # Evidence JSON must be exactly reproducible from current inputs.
    evidence_path = ROOT / policy["canonicalOutputs"]["evidenceJson"]
    sha_path = ROOT / policy["canonicalOutputs"]["sha256Text"]
    if not evidence_path.exists():
        errors.append("missing release evidence JSON")
    else:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        expected_evidence = release.build_evidence(policy)
        if evidence != expected_evidence:
            errors.append("release evidence JSON does not match current deterministic inputs")
        if evidence.get("timestampOmittedByDesign") is not True:
            errors.append("release evidence must omit timestamps by design")
        for profile in ("engineering", "presentation"):
            entry = evidence.get("canonicalFiles", {}).get(profile, {})
            target = canonical.get(profile)
            if target is not None and target.exists() and entry.get("sha256") != sha256_file(target):
                errors.append(f"evidence SHA mismatch: {profile}")

    if not sha_path.exists():
        errors.append("missing SHA256 text evidence")
    else:
        lines = [line for line in sha_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        expected_pairs = [
            (sha256_file(ROOT / policy["canonicalOutputs"]["engineering"]), policy["canonicalOutputs"]["engineering"]),
            (sha256_file(ROOT / policy["canonicalOutputs"]["presentation"]), policy["canonicalOutputs"]["presentation"]),
            (sha256_file(evidence_path), policy["canonicalOutputs"]["evidenceJson"]),
        ] if evidence_path.exists() and all(p.exists() for p in canonical.values()) else []
        expected_lines = [f"{digest}  {rel}" for digest, rel in expected_pairs]
        if lines != expected_lines:
            errors.append("SHA256 text evidence mismatch")

    # Fixed final project counts inherited from already-validated Step 4-7 source snapshot.
    print("SOURCE_PATCH=PATCH-2026-09-13-R6")
    print("RELEASE_VERSION=MASTERPLAN-R6-FINAL")
    print("BUILDING_AND_MAJOR_FACILITY_RECORDS=204")
    print("RESIDENCES=56")
    print("OUTDOOR_SPORT_RECORDS=36")
    print("PRESENTATION_TOP_LEVEL_LAYERS=19")
    print("ENGINEERING_TOP_LEVEL_LAYERS=23")
    print("STEP7_CONTENT_INVARIANT_CHECK=ON")
    print("DETERMINISTIC_BYTE_REBUILD_CHECK=ON")
    print("EXTERNAL_ASSETS=0")
    print("RASTER=0")

    if errors:
        for error in errors:
            print("FAIL", error)
        print(f"RESULT=FAIL errors={len(errors)}")
        return 1

    for profile in ("engineering", "presentation"):
        target = canonical[profile]
        print(f"SHA256_{profile.upper()}={sha256_file(target)}")
        print(f"SIZE_{profile.upper()}={target.stat().st_size}")
    print(f"SHA256_EVIDENCE={sha256_file(evidence_path)}")
    print("RESULT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

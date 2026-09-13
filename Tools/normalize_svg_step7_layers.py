#!/usr/bin/env python3
"""Normalize Step-7 top-level SVG group order for predictable Figma import."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Step7-R6-Engineering.svg",
    ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Step7-R6-Figma.svg",
]

BASE_ORDER = [
    "01_CONTEXT_City_Roads",
    "02_BASE_Campus_Boundary",
    "03_CONTEXT_District_Washes",
    "04_BASE_Perimeter_Wall",
    "05_POI_Gates_Interfaces",
    "06_LANDSCAPE_Green_Structure",
    "07_MOBILITY_Internal_Roads",
    "08_LANDSCAPE_Water",
    "09_LANDSCAPE_Open_Space",
    "10_BUILT_Buildings",
    "11_BUILT_Residential",
    "12_AMENITY_Sports",
    "13_POI_Reference",
    "14_LABEL_Primary_Places",
    "15_LABEL_Secondary_POI",
    "16_LABEL_Districts_Life",
    "17_LABEL_Roads_Water",
    "18_META_Legend",
    "19_META_North_Scale",
]
TECH_ORDER = [
    "90_TECH_Object_Labels",
    "91_TECH_Road_Names",
    "92_LEGACY_Presentation_Labels",
    "93_LEGACY_Step6_Legend",
]


def extract(svg: str, oid: str):
    paired = re.compile(rf'\n?\s*<g id="{re.escape(oid)}"[^>]*>.*?</g>\s*', re.S)
    match = paired.search(svg)
    if match:
        return svg[:match.start()] + "\n" + svg[match.end():], match.group(0).strip()
    self_closing = re.compile(rf'\n?\s*<g id="{re.escape(oid)}"[^>]*/>\s*')
    match = self_closing.search(svg)
    if match:
        return svg[:match.start()] + "\n" + svg[match.end():], match.group(0).strip()
    return svg, None


def normalize(path: Path):
    svg = path.read_text(encoding="utf-8")
    is_engineering = "Engineering.svg" in path.name
    order = BASE_ORDER + (TECH_ORDER if is_engineering else [])
    groups = []
    for oid in order:
        svg, group = extract(svg, oid)
        if group is None:
            raise SystemExit(f"{path.name}: missing delivery layer {oid}")
        groups.append(group)
    if not is_engineering:
        for oid in TECH_ORDER:
            if f'id="{oid}"' in svg:
                raise SystemExit(f"{path.name}: presentation still contains technical layer {oid}")
    svg = svg.replace("</svg>", "\n" + "\n".join(groups) + "\n</svg>", 1)
    path.write_text(svg, encoding="utf-8")
    print(f"NORMALIZED {path.relative_to(ROOT)}")


def main():
    for path in FILES:
        normalize(path)


if __name__ == "__main__":
    main()

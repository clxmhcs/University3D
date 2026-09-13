#!/usr/bin/env python3
"""Validate Step-7 delivery structure while freezing Step-6 engineering geometry."""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import generate_svg_step7 as step7
from normalize_svg_step7_layers import BASE_ORDER, TECH_ORDER

ROOT = Path(__file__).resolve().parents[1]
STEP6_ENGINEERING = ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Step6-R6-Engineering.svg"
STEP6_PRESENTATION = ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Step6-R6-Figma.svg"
STEP7_ENGINEERING = ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Step7-R6-Engineering.svg"
STEP7_PRESENTATION = ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Step7-R6-Figma.svg"
PATCH = "PATCH-2026-09-13-R6"

GEOMETRY_ATTRS = (
    "x", "y", "width", "height", "cx", "cy", "r", "x1", "y1", "x2", "y2",
    "points", "d", "transform", "stroke-width",
    "data-world-x", "data-world-z", "data-length-m", "data-width-m", "data-rotation-y",
    "data-clear-width-m", "data-area-m2", "data-water-level-y",
)


def parse(path):
    return ET.fromstring(Path(path).read_text(encoding="utf-8"))


def local_tag(elem):
    return elem.tag.split("}")[-1]


def index_by_id(root):
    return {e.attrib["id"]: e for e in root.iter() if "id" in e.attrib}


def geometry_index(root):
    out = {}
    for elem in root.iter():
        oid = elem.attrib.get("id")
        if not oid or oid.startswith("STEP7-"):
            continue
        tag = local_tag(elem)
        if tag in {"g", "text", "metadata", "style", "defs", "title", "desc"}:
            continue
        out[oid] = elem
    return out


def compare_geometry(base_path, delivery_path):
    errors = []
    base = geometry_index(parse(base_path))
    delivered = geometry_index(parse(delivery_path))
    for oid, a in base.items():
        b = delivered.get(oid)
        if b is None:
            errors.append(f"{Path(delivery_path).name}: missing Step-6 geometry object {oid}")
            continue
        if local_tag(a) != local_tag(b):
            errors.append(f"{Path(delivery_path).name}: tag changed for {oid}")
            continue
        for attr in GEOMETRY_ATTRS:
            if a.attrib.get(attr) != b.attrib.get(attr):
                errors.append(f"{Path(delivery_path).name}: geometry changed {oid}.{attr}: {a.attrib.get(attr)!r} -> {b.attrib.get(attr)!r}")
                break
    return errors


def top_level_group_ids(root):
    return [c.attrib.get("id") for c in list(root) if local_tag(c) == "g" and c.attrib.get("id")]


def direct_text_count(group):
    return len([e for e in list(group) if local_tag(e) == "text"])


def main():
    core, city_roads, wall, internal, water, cfg, sports, step5_policy, visual_policy, delivery, rows = step7.load_all()
    errors = []

    errors += compare_geometry(STEP6_ENGINEERING, STEP7_ENGINEERING)
    errors += compare_geometry(STEP6_PRESENTATION, STEP7_PRESENTATION)

    eng_text = STEP7_ENGINEERING.read_text(encoding="utf-8")
    fig_text = STEP7_PRESENTATION.read_text(encoding="utf-8")
    for path, text in ((STEP7_ENGINEERING, eng_text), (STEP7_PRESENTATION, fig_text)):
        if PATCH not in text or "step=7" not in text or "generate_svg_step7.py" not in text:
            errors.append(f"{path.name}: missing Step-7 metadata")
        if "<image" in text.lower():
            errors.append(f"{path.name}: raster image element found")

    eng = parse(STEP7_ENGINEERING)
    fig = parse(STEP7_PRESENTATION)
    eng_idx = index_by_id(eng)
    fig_idx = index_by_id(fig)

    expected_eng_order = BASE_ORDER + TECH_ORDER
    expected_fig_order = BASE_ORDER
    actual_eng_order = top_level_group_ids(eng)
    actual_fig_order = top_level_group_ids(fig)
    if actual_eng_order != expected_eng_order:
        errors.append(f"engineering layer order mismatch: {actual_eng_order}")
    if actual_fig_order != expected_fig_order:
        errors.append(f"presentation layer order mismatch: {actual_fig_order}")

    for oid in BASE_ORDER:
        if oid not in eng_idx or oid not in fig_idx:
            errors.append(f"missing delivery layer {oid}")
    for oid in TECH_ORDER:
        if oid not in eng_idx:
            errors.append(f"engineering missing technical layer {oid}")
        if oid in fig_idx:
            errors.append(f"presentation must physically prune technical layer {oid}")

    # Final curated label counts.
    primary = fig_idx.get("14_LABEL_Primary_Places")
    secondary = fig_idx.get("15_LABEL_Secondary_POI")
    district = fig_idx.get("16_LABEL_Districts_Life")
    roads_water = fig_idx.get("17_LABEL_Roads_Water")
    legend = fig_idx.get("18_META_Legend")
    if primary is None or direct_text_count(primary) != len(delivery["primaryPlaces"]):
        errors.append("primary place label count mismatch")
    expected_secondary = len(delivery["secondaryPlaces"]) + len(delivery["lifeServicePOIs"]) + len(core["squares"]) + len(core["parks"]) + 1 + len(core.get("seasonalPaths", []))
    if secondary is None or direct_text_count(secondary) != expected_secondary:
        errors.append(f"secondary label count mismatch expected {expected_secondary}")
    expected_district = len(core["districts"]) + 4 + 2
    if district is None or direct_text_count(district) != expected_district:
        errors.append(f"district/life/axis label count mismatch expected {expected_district}")
    expected_roads_water = len(delivery["roadLabels"]["externalRoadIDs"]) + len(delivery["roadLabels"]["internalRoadIDs"]) + len(water["waterBodies"])
    if roads_water is None or direct_text_count(roads_water) != expected_roads_water:
        errors.append(f"road/water label count mismatch expected {expected_roads_water}")
    if legend is None:
        errors.append("presentation legend missing")

    # Technical ID labels must be absent from presentation, not merely hidden with CSS.
    forbidden_classes = {"building-id", "residence-id", "sport-id", "hospital-id"}
    for elem in fig.iter():
        if local_tag(elem) != "text":
            continue
        classes = set(elem.attrib.get("class", "").split())
        if classes & forbidden_classes:
            errors.append(f"presentation retains technical text class {classes & forbidden_classes}")
            break

    # Current formal naming checks.
    required_text = [
        "博雅图书馆", "江城大学行政中心", "明德会堂", "江城大学综合体育馆",
        "江城大学戏剧表演中心", "江城大学附属医院", "江城大学校园商业中心",
        "西苑食堂", "北苑食堂", "东苑食堂", "南苑食堂",
        "江大校园超市·西苑店", "江大校园超市·北苑店", "江大校园超市·东苑店", "江大校园超市·南苑店",
        "澄湖", "大学路", "学府路", "致远路", "长虹路"
    ]
    for text in required_text:
        if text not in fig_text:
            errors.append(f"presentation missing formal label: {text}")

    deprecated_text = ["西生活区", "北生活区", "东生活区", "南生活区"]
    for text in deprecated_text:
        # Metadata/source notes may contain old terms in older embedded data only if copied; final presentation labels may not.
        for elem in fig.iter():
            if local_tag(elem) == "text" and elem.text and text in elem.text:
                errors.append(f"presentation reintroduces deprecated display name: {text}")
                break

    # Overview road label policy excludes connector and transit-only clutter.
    final_road_texts = [e.text or "" for e in list(roads_water or []) if local_tag(e) == "text" and e.attrib.get("id", "").startswith("STEP7-ROAD-")]
    if any(("连接" in t or "公交优先廊道" in t) for t in final_road_texts):
        errors.append("presentation road labels contain connector/transit-only clutter")

    # No external font/image dependencies.
    if re.search(r'<(?:image|use)\b[^>]*(?:href|xlink:href)="https?://', fig_text, re.I):
        errors.append("presentation contains external linked asset")
    if "@font-face" in fig_text:
        errors.append("presentation embeds external/custom font-face")

    print(f"FIGMA_BASE_LAYERS={13}")
    print(f"PRIMARY_PLACE_LABELS={len(delivery['primaryPlaces'])}")
    print(f"SECONDARY_POI_LABELS={expected_secondary}")
    print(f"DISTRICT_LIFE_AXIS_LABELS={expected_district}")
    print(f"ROAD_WATER_LABELS={expected_roads_water}")
    print("PRESENTATION_TECH_LABELS_PHYSICALLY_PRUNED=ON")
    print("STEP6_GEOMETRY_IMMUTABLE_CHECK=ON")
    if errors:
        for error in errors:
            print("FAIL", error)
        print(f"RESULT=FAIL errors={len(errors)}")
        return 1
    print("RASTER=0")
    print("RESULT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

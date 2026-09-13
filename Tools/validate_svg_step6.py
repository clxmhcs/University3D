#!/usr/bin/env python3
"""Validate Step-6 presentation refinement while freezing Step-5 engineering geometry."""
from __future__ import annotations

import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import generate_svg_step5 as step5
import generate_svg_step6 as step6
from svg_coordinates import SvgCoordinateSystem

ROOT = Path(__file__).resolve().parents[1]
STEP5_ENGINEERING = ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Step5-R6-Engineering.svg"
STEP5_PRESENTATION = ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Step5-R6-Figma.svg"
STEP6_ENGINEERING = ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Step6-R6-Engineering.svg"
STEP6_PRESENTATION = ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Step6-R6-Figma.svg"
PATCH = "PATCH-2026-09-13-R6"

GEOMETRY_ATTRS = (
    "x", "y", "width", "height", "cx", "cy", "r", "x1", "y1", "x2", "y2",
    "points", "transform", "stroke-width",
    "data-world-x", "data-world-z", "data-length-m", "data-width-m", "data-rotation-y",
    "data-clear-width-m", "data-area-m2", "data-water-level-y",
)


def parse(path):
    return ET.fromstring(Path(path).read_text(encoding="utf-8"))


def index_by_id(root):
    return {elem.attrib["id"]: elem for elem in root.iter() if "id" in elem.attrib}


def local_tag(elem):
    return elem.tag.split("}")[-1]


def nearly(a, b, tol=0.03):
    return abs(float(a) - float(b)) <= tol


def compare_step5_geometry(step5_path, step6_path):
    errors = []
    base = index_by_id(parse(step5_path))
    refined = index_by_id(parse(step6_path))
    for oid, a in base.items():
        b = refined.get(oid)
        if b is None:
            errors.append(f"{Path(step6_path).name}: missing Step-5 object {oid}")
            continue
        if local_tag(a) != local_tag(b):
            errors.append(f"{Path(step6_path).name}: tag changed for {oid}")
            continue
        for attr in GEOMETRY_ATTRS:
            av, bv = a.attrib.get(attr), b.attrib.get(attr)
            if av != bv:
                errors.append(f"{Path(step6_path).name}: geometry attr changed {oid}.{attr}: {av!r} -> {bv!r}")
                break
    return errors


def get(root, oid):
    return index_by_id(root).get(oid)


def main():
    core, city_roads, wall, internal, water, cfg, sports, step5_policy, visual_policy, rows = step6.load_all()
    cs = SvgCoordinateSystem.from_file(step5.COORD)
    errors = []

    # 1. Step 5 geometry is immutable in both profiles.
    errors += compare_step5_geometry(STEP5_ENGINEERING, STEP6_ENGINEERING)
    errors += compare_step5_geometry(STEP5_PRESENTATION, STEP6_PRESENTATION)

    # 2. Basic output/metadata/raster rules.
    eng_text = STEP6_ENGINEERING.read_text(encoding="utf-8")
    fig_text = STEP6_PRESENTATION.read_text(encoding="utf-8")
    for path, text in ((STEP6_ENGINEERING, eng_text), (STEP6_PRESENTATION, fig_text)):
        if PATCH not in text or "step=6" not in text or "generate_svg_step6.py" not in text:
            errors.append(f"{path.name}: missing Step-6 metadata")
        if "<image" in text.lower():
            errors.append(f"{path.name}: raster image element found")

    eng = parse(STEP6_ENGINEERING)
    fig = parse(STEP6_PRESENTATION)
    eng_index, fig_index = index_by_id(eng), index_by_id(fig)
    for layer in ("15_DistrictIdentity", "16_GreenStructure", "17_PresentationLabels", "18_Step6Legend"):
        if layer not in eng_index:
            errors.append(f"engineering: missing Step-6 layer {layer}")
        if layer not in fig_index:
            errors.append(f"presentation: missing Step-6 layer {layer}")

    # Engineering profile must not silently gain reference geometry.
    for layer in ("15_DistrictIdentity", "16_GreenStructure", "17_PresentationLabels", "18_Step6Legend"):
        elem = eng_index.get(layer)
        if elem is not None and list(elem):
            errors.append(f"engineering: {layer} must remain empty/reference-omitted")

    # 3. Building visual assignment is complete and unambiguous.
    assignments = step6.building_style_assignment(rows, visual_policy, step5_policy)
    if len(assignments) != 142:
        errors.append(f"building style assignment count {len(assignments)} != 142")
    if assignments.get("LIFE-01") != "science" or assignments.get("LIFE-02") != "science":
        errors.append("LIFE-01/LIFE-02 must be science, not student-life facilities")
    for rid in ("LIFE-C-01", "LIFE-W-01", "LIFE-N-01", "LIFE-E-01", "LIFE-S-01"):
        if assignments.get(rid) != "life":
            errors.append(f"{rid} must use life visual group")

    # 4. District reference envelopes: every district with source x/z ranges, and no invented north-life x range.
    expected_districts = [d for d in core["districts"] if "xRange" in d and "zRange" in d]
    district_elems = [e for oid, e in fig_index.items() if oid.startswith("STEP6-DIST-")]
    if len(district_elems) != len(expected_districts):
        errors.append(f"district envelope count {len(district_elems)} != {len(expected_districts)}")
    if "STEP6-DIST-DIST-NORTH-LIFE" in fig_index:
        errors.append("north-life district rectangle invented despite missing source xRange")
    for district in expected_districts:
        oid = f"STEP6-{district['id']}"
        elem = fig_index.get(oid)
        if elem is None:
            errors.append(f"missing district reference {oid}")
            continue
        x, y, w, h = step6.world_rect_from_ranges(cs, "presentation", district["xRange"], district["zRange"])
        for attr, expected in (("x", x), ("y", y), ("width", w), ("height", h)):
            if not nearly(elem.attrib.get(attr, -99999), expected):
                errors.append(f"{oid}.{attr} mismatch")
                break
        if elem.attrib.get("data-geometry") != "source-control-range":
            errors.append(f"{oid} must stay reference-only source-control-range")

    # 5. Four life-green-heart range rings use residence centroids and preserve 2-4ha uncertainty.
    area_min, area_max = map(float, visual_policy["landscapeSystem"]["lifeGreenHeartAreaHaRange"])
    r_min, r_max = step6.area_radius(area_min), step6.area_radius(area_max)
    for key, life in visual_policy["landscapeSystem"]["formalLifeAreas"].items():
        cx, cz, count = step6.residence_centroid(rows, life["residencePrefix"])
        sx, sy = cs.world_to_svg(cx, cz, "presentation")
        inner = fig_index.get(f"STEP6-GREENHEART-{key.upper()}-INNER")
        outer = fig_index.get(f"STEP6-GREENHEART-{key.upper()}-OUTER")
        if inner is None or outer is None:
            errors.append(f"missing green-heart range for {key}")
            continue
        for elem, radius in ((inner, r_min), (outer, r_max)):
            if not (nearly(elem.attrib.get("cx", -1), sx) and nearly(elem.attrib.get("cy", -1), sy) and nearly(elem.attrib.get("r", -1), radius)):
                errors.append(f"green-heart geometry mismatch for {key}")
        if int(inner.attrib.get("data-residence-count", "-1")) != count:
            errors.append(f"green-heart residence count mismatch for {key}")

    # 6. Two presentation axes and riparian buffers follow source-supported anchors/water.
    for oid in ("STEP6-AXIS-CEREMONIAL", "STEP6-AXIS-ECOLOGICAL", "STEP6-RIPARIAN-LAKE", "STEP6-RIPARIAN-STREAM-NORTH", "STEP6-RIPARIAN-STREAM-SOUTHEAST"):
        if oid not in fig_index:
            errors.append(f"missing presentation landscape object {oid}")

    # 7. Seasonal tree symbols are deterministically derived from source paths.
    expected_tree_count = 0
    seasonal_by_id = {p["id"]: p for p in core.get("seasonalPaths", [])}
    for path_id, avenue in visual_policy["landscapeSystem"]["seasonalAvenues"].items():
        samples = step6.sample_polyline(seasonal_by_id[path_id]["centerlineXZ"], float(avenue["symbolSpacingMeters"]))
        expected_tree_count += len(samples) * 2
    actual_tree_count = len([oid for oid in fig_index if oid.startswith("STEP6-TREE-")])
    if actual_tree_count != expected_tree_count:
        errors.append(f"seasonal tree symbol count {actual_tree_count} != {expected_tree_count}")

    # 8. Labels: every district gets a name; major landmarks get readable names in Figma profile.
    for district in core["districts"]:
        if f"STEP6-LABEL-{district['id']}" not in fig_index:
            errors.append(f"missing district label {district['id']}")
    for rid in step6.MAJOR_LABEL_IDS:
        if f"STEP6-MAJOR-{rid}" not in fig_index:
            errors.append(f"missing major-place label {rid}")

    if ".building-id,.residence-id,.sport-id { display:none; }" not in fig_text:
        errors.append("presentation profile must hide dense engineering IDs")

    print(f"BUILDING_STYLE_ASSIGNMENTS={len(assignments)}")
    print(f"DISTRICT_REFERENCE_ENVELOPES={len(expected_districts)}")
    print("LIFE_GREEN_HEARTS=4 area_range_ha=2-4")
    print("LANDSCAPE_AXES=2")
    print(f"SEASONAL_TREE_SYMBOLS={actual_tree_count}")
    print("STEP5_GEOMETRY_IMMUTABLE_CHECK=ON")
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

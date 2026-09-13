#!/usr/bin/env python3
"""Validate Step-5 building, residence and sports SVG layers."""
from __future__ import annotations

import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from svg_coordinates import SvgCoordinateSystem

ROOT = Path(__file__).resolve().parents[1]
PATCH = "PATCH-2026-09-13-R6"
BUILDINGS = ROOT / "CampusData/svg/building_placement_r6.csv"
SPORTS = ROOT / "CampusData/svg/outdoor_sports_r6.json"
POLICY = ROOT / "CampusData/svg/step5_render_policy_r6.json"
COORD = ROOT / "CampusData/svg/svg_coordinate_system_r6.json"
STEP4_ENGINEERING = ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Step4-R6-Engineering.svg"
STEP4_FIGMA = ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Step4-R6-Figma.svg"
STEP5_ENGINEERING = ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Step5-R6-Engineering.svg"
STEP5_FIGMA = ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Step5-R6-Figma.svg"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def find_id(root, oid):
    for elem in root.iter():
        if elem.attrib.get("id") == oid:
            return elem
    return None


def nearly(a, b, tol=0.02):
    return abs(float(a) - float(b)) <= tol


def rect_center(elem):
    return (
        float(elem.attrib["x"]) + float(elem.attrib["width"]) / 2.0,
        float(elem.attrib["y"]) + float(elem.attrib["height"]) / 2.0,
    )


def rotation_from_transform(elem):
    m = re.search(r"rotate\(([-+0-9.]+)", elem.attrib.get("transform", ""))
    if not m:
        raise ValueError(f"missing rotation transform for {elem.attrib.get('id')}")
    return float(m.group(1)) % 360.0


def extract_group(text, gid):
    marker = f'<g id="{gid}"'
    start = text.find(marker)
    if start < 0:
        return None
    end = text.find("</g>", start)
    if end < 0:
        return None
    return text[start:end + 4]


def validate_step4_unchanged(step4_text, step5_text, errors, label):
    for gid in ["01_CityRoads", "02_CampusBoundary", "03_PerimeterWall", "04_Gates", "05_InternalRoads", "06_Water", "07_Landscape"]:
        a = extract_group(step4_text, gid)
        b = extract_group(step5_text, gid)
        if a is None or b is None or a != b:
            errors.append(f"{label}: Step 4 geometry changed in {gid}")


def validate_file(path, step4_path, profile, rows, sports, policy, cs):
    errors = []
    text = Path(path).read_text(encoding="utf-8")
    step4_text = Path(step4_path).read_text(encoding="utf-8")
    root = ET.fromstring(text)

    def check(ok, msg):
        if not ok:
            errors.append(f"{Path(path).name}: {msg}")

    expected_size = (3600, 2800) if profile == "engineering" else (4200, 3200)
    check(root.attrib.get("width") == str(expected_size[0]), "width mismatch")
    check(root.attrib.get("height") == str(expected_size[1]), "height mismatch")
    check(root.attrib.get("viewBox") == f"0 0 {expected_size[0]} {expected_size[1]}", "viewBox mismatch")
    check(PATCH in text, "missing R6 metadata")
    check("step=5" in text, "missing Step 5 metadata")
    check("<image" not in text.lower(), "raster image found")
    validate_step4_unchanged(step4_text, text, errors, Path(path).name)

    # XML IDs must be unique.
    ids = []
    for elem in root.iter():
        oid = elem.attrib.get("id")
        if oid:
            ids.append(oid)
    dup = sorted({x for x in ids if ids.count(x) > 1})
    check(not dup, f"duplicate XML IDs: {dup}")

    residences = [r for r in rows if r["id"].startswith("RES-")]
    counts = {}
    for row in residences:
        counts[row["residenceType"]] = counts.get(row["residenceType"], 0) + 1
    check(len(rows) == 204, f"building/facility records={len(rows)} expected 204")
    check(len(residences) == 56, f"residences={len(residences)} expected 56")
    check(counts == {"graduate": 10, "international": 4, "undergraduate": 42}, f"residence type counts mismatch {counts}")

    routed = set(policy["buildingTableSpecialRouting"]["sportsSurfaceIDs"]) | set(policy["buildingTableSpecialRouting"]["sportsStandIDs"])
    overlay = {x["id"]: x for x in policy["hospitalOverlays"]}

    # Buildings / major facilities not routed to residence or sports layers.
    for row in rows:
        bid = row["id"]
        if bid.startswith("RES-") or bid in routed:
            continue
        elem = find_id(root, bid)
        check(elem is not None, f"missing building {bid}")
        if elem is None:
            continue
        if bid in overlay:
            ov = overlay[bid]
            expected_center = cs.world_to_svg(ov["planCenterXZ"][0], ov["planCenterXZ"][1], profile)
            actual_center = rect_center(elem)
            check(nearly(actual_center[0], expected_center[0]) and nearly(actual_center[1], expected_center[1]), "HSP-02 plan center mismatch")
            check(nearly(elem.attrib["width"], ov["lengthMeters"]), "HSP-02 length mismatch")
            check(nearly(elem.attrib["height"], ov["widthMeters"]), "HSP-02 width mismatch")
            check(elem.attrib.get("data-ground-independent") == "false", "HSP-02 must not be independent ground footprint")
            check(elem.attrib.get("data-parent-id") == "HSP-01", "HSP-02 parent mismatch")
            check(nearly(rotation_from_transform(elem), ov["rotationY"]), "HSP-02 rotation mismatch")
            obsolete = cs.world_to_svg(-1280, -830, profile)
            check(not (nearly(actual_center[0], obsolete[0]) and nearly(actual_center[1], obsolete[1])), "HSP-02 leaked to obsolete ground parcel")
        else:
            x, z = float(row["x"]), float(row["z"])
            expected_center = cs.world_to_svg(x, z, profile)
            actual_center = rect_center(elem)
            check(nearly(actual_center[0], expected_center[0]) and nearly(actual_center[1], expected_center[1]), f"{bid} center mismatch")
            check(nearly(elem.attrib["width"], row["length"]), f"{bid} length mismatch")
            check(nearly(elem.attrib["height"], row["width"]), f"{bid} width mismatch")
            check(nearly(rotation_from_transform(elem), row["rotationY"]), f"{bid} rotation mismatch")

    # Residence rendering policies.
    rp = policy["residenceFootprints"]
    for row in residences:
        bid = row["id"]
        elem = find_id(root, bid)
        check(elem is not None, f"missing residence {bid}")
        if elem is None:
            continue
        center_expected = cs.world_to_svg(float(row["x"]), float(row["z"]), profile)
        center_actual = rect_center(elem)
        check(nearly(center_actual[0], center_expected[0]) and nearly(center_actual[1], center_expected[1]), f"{bid} center mismatch")
        check(nearly(rotation_from_transform(elem), row["rotationY"]), f"{bid} rotation mismatch")
        kind = row["residenceType"]
        p = rp[kind]
        if kind == "undergraduate":
            check(nearly(elem.attrib["width"], p["lengthMinMeters"]), f"{bid} min length mismatch")
            check(nearly(elem.attrib["height"], p["widthMeters"]), f"{bid} width mismatch")
            check(elem.attrib.get("data-render-mode") == "range-not-midpoint", f"{bid} must preserve range")
            max_elem = find_id(root, f"{bid}-MAX")
            check(max_elem is not None, f"missing max envelope for {bid}")
            if max_elem is not None:
                check(nearly(max_elem.attrib["width"], p["lengthMaxMeters"]), f"{bid} max length mismatch")
                check(nearly(max_elem.attrib["height"], p["widthMeters"]), f"{bid} max width mismatch")
        else:
            check(nearly(elem.attrib["width"], p["lengthMeters"]), f"{bid} length mismatch")
            check(nearly(elem.attrib["height"], p["widthMeters"]), f"{bid} width mismatch")

    # Routed major sports table records.
    for bid in routed:
        elem = find_id(root, bid)
        check(elem is not None, f"missing routed sports record {bid}")
        check(find_id(root, f"{bid}-MAX") is None, f"unexpected range envelope for sports {bid}")

    # R6 outdoor sports.
    marker_only_expected = set(policy["outdoorSports"]["markerOnlyIDs"])
    marker_only_seen = set()
    footprint_seen = 0
    for item in sports["outdoorSports"]:
        oid = item["id"]
        elem = find_id(root, oid)
        check(elem is not None, f"missing outdoor sport {oid}")
        if elem is None:
            continue
        expected_center = cs.world_to_svg(item["position"]["x"], item["position"]["z"], profile)
        if item.get("controlFootprint"):
            footprint_seen += 1
            actual_center = rect_center(elem)
            check(nearly(actual_center[0], expected_center[0]) and nearly(actual_center[1], expected_center[1]), f"{oid} center mismatch")
            check(nearly(elem.attrib["width"], item["controlFootprint"]["length"]), f"{oid} length mismatch")
            check(nearly(elem.attrib["height"], item["controlFootprint"]["width"]), f"{oid} width mismatch")
            check(nearly(rotation_from_transform(elem), item.get("rotationY", 0)), f"{oid} rotation mismatch")
        else:
            marker_only_seen.add(oid)
            check(elem.tag.endswith("circle"), f"{oid} without footprint must be marker-only circle")
            check(elem.attrib.get("data-geometry") == "center-marker-only", f"{oid} marker-only flag missing")
            check(nearly(elem.attrib["cx"], expected_center[0]) and nearly(elem.attrib["cy"], expected_center[1]), f"{oid} marker center mismatch")
    check(marker_only_seen == marker_only_expected, f"marker-only sports mismatch {marker_only_seen}")
    check(footprint_seen == len(sports["outdoorSports"]) - len(marker_only_expected), "outdoor sports footprint count mismatch")

    totals = sports["outdoorSportsTotals"]
    check(totals == {
        "basketballFullCourtEquivalent": 44,
        "outdoorTableTennisTables": 158,
        "tennisCourts": 16,
        "volleyballCourts": 22,
        "outdoorBadmintonCourts": 16,
        "fiveASideFootballFields": 6,
    }, "sports totals mismatch")

    # Reserve parcel point is policy driven and must not contain an HSP-02 ground rectangle.
    reserve = policy["hospitalReserveParcel"]
    reserve_elem = find_id(root, reserve["id"])
    check(reserve_elem is not None, "missing HSP-RSV-01 reserve marker")
    if reserve_elem is not None:
        expected = cs.world_to_svg(reserve["centerXZ"][0], reserve["centerXZ"][1], profile)
        check(nearly(reserve_elem.attrib["cx"], expected[0]) and nearly(reserve_elem.attrib["cy"], expected[1]), "reserve parcel marker mismatch")

    for layer in ["08_Buildings", "09_Residential", "10_Sports", "11_POI", "12_Labels"]:
        check(find_id(root, layer) is not None, f"missing layer {layer}")

    return errors


def main():
    rows = load_csv(BUILDINGS)
    sports = load_json(SPORTS)
    policy = load_json(POLICY)
    cs = SvgCoordinateSystem.from_file(COORD)
    errors = []
    errors += validate_file(STEP5_ENGINEERING, STEP4_ENGINEERING, "engineering", rows, sports, policy, cs)
    errors += validate_file(STEP5_FIGMA, STEP4_FIGMA, "presentation", rows, sports, policy, cs)

    residence_counts = {}
    for row in rows:
        if row["id"].startswith("RES-"):
            residence_counts[row["residenceType"]] = residence_counts.get(row["residenceType"], 0) + 1
    marker_only = [x for x in sports["outdoorSports"] if not x.get("controlFootprint")]
    print(f"BUILDING_AND_MAJOR_FACILITY_RECORDS={len(rows)}")
    print(f"RESIDENCES={sum(residence_counts.values())} TYPES={residence_counts}")
    print(f"OUTDOOR_SPORT_RECORDS={len(sports['outdoorSports'])}")
    print(f"SPORT_MARKER_ONLY={len(marker_only)}")
    print("STEP4_GEOMETRY_IMMUTABLE_CHECK=ON")
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

#!/usr/bin/env python3
"""Validate Step-4 Jiangcheng University SVG outputs against frozen source data."""
from __future__ import annotations

import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from svg_coordinates import SvgCoordinateSystem
from generate_svg_step4 import offset_closed_polygon

ROOT = Path(__file__).resolve().parents[1]
PATCH = "PATCH-2026-09-13-R6"
CORE = ROOT / "CampusData/svg/core_geometry_r6.json"
INTERNAL = ROOT / "CampusData/svg/internal_roads_r3.json"
WATER = ROOT / "CampusData/svg/water_r6.json"
COORD = ROOT / "CampusData/svg/svg_coordinate_system_r6.json"
ENGINEERING = ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Step4-R6-Engineering.svg"
FIGMA = ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Step4-R6-Figma.svg"
NS = {"svg": "http://www.w3.org/2000/svg"}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_points(text):
    out = []
    for token in text.strip().split():
        x, y = token.split(",")
        out.append((float(x), float(y)))
    return out


def nearly(a, b, tol=0.02):
    return abs(float(a) - float(b)) <= tol


def find_by_id(root, oid):
    for elem in root.iter():
        if elem.attrib.get("id") == oid:
            return elem
    return None


def validate_file(path, profile, core, internal, water, cs):
    errors = []
    text = Path(path).read_text(encoding="utf-8")
    root = ET.fromstring(text)

    def check(ok, msg):
        if not ok:
            errors.append(f"{Path(path).name}: {msg}")

    expected_size = (3600, 2800) if profile == "engineering" else (4200, 3200)
    check(root.attrib.get("width") == str(expected_size[0]), "width mismatch")
    check(root.attrib.get("height") == str(expected_size[1]), "height mismatch")
    check(root.attrib.get("viewBox") == f"0 0 {expected_size[0]} {expected_size[1]}", "viewBox mismatch")
    check(PATCH in text, "missing R6 patch metadata")
    check("step=4" in text, "missing Step 4 metadata")
    check("<image" not in text.lower(), "raster image element found")

    # Internal roads: every source ID must exist exactly once.
    for road in internal["internalRoads"]:
        elem = find_by_id(root, road["id"])
        check(elem is not None, f"missing internal road {road['id']}")
        if elem is None:
            continue
        check(nearly(elem.attrib.get("data-width-m", -1), road["width"]), f"{road['id']} width mismatch")
        if road["id"] != "PATH-CHENGHU":
            source_pts = [cs.world_to_svg(p[0], p[1], profile) for p in road["centerlineXZ"]]
            svg_pts = parse_points(elem.attrib["points"])
            check(len(source_pts) == len(svg_pts), f"{road['id']} point count mismatch")
            if len(source_pts) == len(svg_pts):
                for i, (a, b) in enumerate(zip(source_pts, svg_pts)):
                    if not (nearly(a[0], b[0]) and nearly(a[1], b[1])):
                        errors.append(f"{Path(path).name}: {road['id']} point {i} mismatch")
                        break

    # Derived Chenghu path must be source-shoreline offset 25m.
    lake = next(w for w in water["waterBodies"] if w["id"] == "WATER-LAKE-01")
    path_elem = find_by_id(root, "PATH-CHENGHU")
    if path_elem is not None:
        derived = offset_closed_polygon(lake["shorelineXZ"], 25.0)
        derived = derived + [derived[0]]
        expected = [cs.world_to_svg(p[0], p[1], profile) for p in derived]
        actual = parse_points(path_elem.attrib["points"])
        check(len(expected) == len(actual), "PATH-CHENGHU point count mismatch")
        if len(expected) == len(actual):
            for i, (a, b) in enumerate(zip(expected, actual)):
                if not (nearly(a[0], b[0]) and nearly(a[1], b[1])):
                    errors.append(f"{Path(path).name}: PATH-CHENGHU point {i} mismatch")
                    break

    # Transit and junction inventory.
    for stop in internal["busStops"]:
        check(find_by_id(root, stop["id"]) is not None, f"missing bus stop {stop['id']}")
    for jct in internal["junctions"]:
        check(find_by_id(root, jct["id"]) is not None, f"missing junction {jct['id']}")

    # Water inventory.
    for body in water["waterBodies"]:
        elem = find_by_id(root, body["id"])
        check(elem is not None, f"missing water body {body['id']}")
    check(find_by_id(root, "WATER-STREAM-MAIN-NORTH") is not None, "missing north main-stream chain")
    check(find_by_id(root, "WATER-STREAM-MAIN-SOUTHEAST") is not None, "missing southeast main-stream chain")
    exact_lake = find_by_id(root, "WATER-LAKE-01")
    if exact_lake is not None:
        check(exact_lake.attrib.get("data-geometry") == "exact-shoreline", "Chenghu must use exact shoreline")
        expected = [cs.world_to_svg(p[0], p[1], profile) for p in lake["shorelineXZ"]]
        actual = parse_points(exact_lake.attrib["points"])
        check(len(expected) == len(actual), "Chenghu shoreline point count mismatch")

    # Other water bodies cannot pretend to have frozen shorelines.
    for body in water["waterBodies"]:
        if body["id"] == "WATER-LAKE-01":
            continue
        elem = find_by_id(root, body["id"])
        if elem is not None:
            check(elem.attrib.get("data-geometry") == "area-equivalent-reference-circle", f"{body['id']} geometry must remain reference-only")

    # Major open-space records supported by core source.
    for i, _ in enumerate(core["squares"], 1):
        check(find_by_id(root, f"SQUARE-{i:02d}") is not None, f"missing square marker {i}")
    for i, _ in enumerate(core["parks"], 1):
        check(find_by_id(root, f"PARK-{i:02d}") is not None, f"missing park reference {i}")
    check(find_by_id(root, core["centralLawn"]["id"]) is not None, "missing Boya lawn envelope")
    for seasonal in core.get("seasonalPaths", []):
        check(find_by_id(root, seasonal["id"]) is not None, f"missing seasonal path {seasonal['id']}")

    # Stable layer structure.
    for layer in ("05_InternalRoads", "06_Water", "07_Landscape", "08_Buildings", "09_Residential", "10_Sports", "11_POI", "12_Labels"):
        check(find_by_id(root, layer) is not None, f"missing layer {layer}")

    return errors


def main():
    core, internal, water = load_json(CORE), load_json(INTERNAL), load_json(WATER)
    cs = SvgCoordinateSystem.from_file(COORD)
    errors = []
    errors += validate_file(ENGINEERING, "engineering", core, internal, water, cs)
    errors += validate_file(FIGMA, "presentation", core, internal, water, cs)
    print(f"INTERNAL_ROADS={len(internal['internalRoads'])}")
    print(f"BUS_STOPS={len(internal['busStops'])}")
    print(f"JUNCTIONS={len(internal['junctions'])}")
    print(f"WATER_BODIES={len(water['waterBodies'])}")
    print(f"SQUARE_MARKERS={len(core['squares'])}")
    print(f"PARK_REFERENCES={len(core['parks'])}")
    print(f"SEASONAL_PATHS={len(core.get('seasonalPaths', []))}")
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

#!/usr/bin/env python3
"""Validate the committed Step-3 engineering SVG against frozen R6 source data."""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from svg_coordinates import SvgCoordinateSystem

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "Artifacts/SVG/Jiangcheng-University-MasterPlan-Skeleton-R6-Engineering.svg"
CORE = ROOT / "CampusData/svg/core_geometry_r6.json"
ROADS = ROOT / "CampusData/transport/external_roads.json"
WALL = ROOT / "CampusData/landscape/perimeter_wall.json"
COORD = ROOT / "CampusData/svg/svg_coordinate_system_r6.json"
PATCH = "PATCH-2026-09-13-R6"
NS = {"svg": "http://www.w3.org/2000/svg"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_points(value):
    out = []
    for token in value.strip().split():
        x, y = token.split(",")
        out.append((float(x), float(y)))
    return out


def close(a, b, tol=0.02):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def main():
    core, roads, wall, coord = map(load, (CORE, ROADS, WALL, COORD))
    errors = []
    for name, source in (("core", core), ("roads", roads), ("wall", wall), ("coord", coord)):
        if source.get("sourcePatchVersion") != PATCH:
            errors.append(f"{name}: patch mismatch")

    root = ET.parse(SVG).getroot()
    if root.attrib.get("viewBox") != "0 0 3600 2800":
        errors.append(f"viewBox={root.attrib.get('viewBox')} expected 0 0 3600 2800")
    if root.findall(".//svg:image", NS):
        errors.append("raster <image> element is forbidden")

    expected_groups = [
        "01_CityRoads", "02_CampusBoundary", "03_PerimeterWall", "04_Gates",
        "05_InternalRoads", "06_Water", "07_Landscape", "08_Buildings",
        "09_Residential", "10_Sports", "11_POI", "12_Labels", "13_RoadNames", "14_Legend",
    ]
    ids = {node.attrib.get("id") for node in root.iter() if node.attrib.get("id")}
    for gid in expected_groups:
        if gid not in ids:
            errors.append(f"missing root group {gid}")

    cs = SvgCoordinateSystem.from_file(COORD)
    boundary = root.find(".//svg:polygon[@id='CAMPUS-01-BOUNDARY']", NS)
    if boundary is None:
        errors.append("missing CAMPUS-01-BOUNDARY")
    else:
        actual = parse_points(boundary.attrib["points"])
        expected = cs.world_points_to_svg(core["campus"]["boundaryXZ"], "engineering")
        if len(actual) != 16:
            errors.append(f"boundary point count={len(actual)} expected 16")
        elif any(not close(a, b) for a, b in zip(actual, expected)):
            errors.append("campus boundary SVG coordinates diverge from R6 source")

    for road in roads["roads"]:
        node = root.find(f".//svg:polyline[@id='{road['id']}']", NS)
        if node is None:
            errors.append(f"missing road {road['id']}")
            continue
        actual = parse_points(node.attrib["points"])
        expected = cs.world_points_to_svg(road["centerlineXZ"], "engineering")
        if len(actual) != len(expected) or any(not close(a, b) for a, b in zip(actual, expected)):
            errors.append(f"{road['id']} geometry diverges from R6 source")
        if node.attrib.get("data-width-m") != "36":
            errors.append(f"{road['id']} width metadata != 36m")

    opening_targets = [x["targetID"] for x in wall["openings"]]
    if len(opening_targets) != 9:
        errors.append(f"source wall openings={len(opening_targets)} expected 9")
    entrance_by_id = {e["id"]: e for e in core["entrances"]}
    for target in opening_targets:
        marker = root.find(f".//*[@id='{target}']", NS)
        access = root.find(f".//*[@id='ACCESS-{target}']", NS)
        if marker is None:
            errors.append(f"missing gate/interface marker {target}")
        else:
            source = entrance_by_id.get(target)
            if source is None:
                errors.append(f"source entrance missing {target}")
            else:
                expected = cs.world_to_svg(source["position"]["x"], source["position"]["z"], "engineering")
                actual = (float(marker.attrib["cx"]), float(marker.attrib["cy"]))
                if not close(actual, expected):
                    errors.append(f"{target} marker coordinate mismatch")
        if access is None:
            errors.append(f"missing wall-opening access connector for {target}")

    wall_parts = [n for n in root.findall(".//svg:polyline", NS) if n.attrib.get("data-source-wall")]
    if len(wall_parts) != 13:
        errors.append(f"wall visible parts={len(wall_parts)} expected 13 after 9 openings")

    expected_known = {
        "GATE-SOUTH": (1800, 2498), "GATE-NORTH": (1800, 258),
        "GATE-WEST": (252, 1480), "GATE-EAST": (3355, 1280),
    }
    for target, expected in expected_known.items():
        node = root.find(f".//*[@id='{target}']", NS)
        if node is not None and not close((float(node.attrib["cx"]), float(node.attrib["cy"])), expected):
            errors.append(f"known coordinate check failed: {target}")

    text = SVG.read_text(encoding="utf-8")
    if "PATCH-2026-09-13-R6" not in text or "noRaster=true" not in text:
        errors.append("SVG provenance metadata missing")

    print(f"SVG={SVG.relative_to(ROOT)}")
    print("VIEWBOX=3600x2800")
    print(f"CITY_ROADS={len(roads['roads'])}")
    print(f"BOUNDARY_POINTS={len(core['campus']['boundaryXZ'])}")
    print(f"WALL_OPENINGS={len(opening_targets)}")
    print(f"WALL_VISIBLE_PARTS={len(wall_parts)}")
    if errors:
        for error in errors:
            print("FAIL", error)
        print(f"RESULT=FAIL errors={len(errors)}")
        return 1
    print("RESULT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

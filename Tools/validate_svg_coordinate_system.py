#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Tools"))

from svg_coordinates import SvgCoordinateSystem  # noqa: E402

CONFIG = ROOT / "CampusData/svg/svg_coordinate_system_r6.json"
CORE = ROOT / "CampusData/svg/core_geometry_r6.json"
EXTERNAL = ROOT / "CampusData/transport/external_roads.json"
EXPECTED_PATCH = "PATCH-2026-09-13-R6"


def close_pair(a, b, tol=1e-9):
    return abs(a[0]-b[0]) <= tol and abs(a[1]-b[1]) <= tol


def main() -> int:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    core = json.loads(CORE.read_text(encoding="utf-8"))
    ext = json.loads(EXTERNAL.read_text(encoding="utf-8"))
    cs = SvgCoordinateSystem.from_file(CONFIG)
    errors: list[str] = []

    def check(ok: bool, message: str):
        if not ok:
            errors.append(message)

    check(cfg["sourcePatchVersion"] == EXPECTED_PATCH, "coordinate config patch is not R6")
    check(core["sourcePatchVersion"] == EXPECTED_PATCH, "core geometry patch is not R6")
    check(ext["sourcePatchVersion"] == EXPECTED_PATCH, "external roads patch is not R6")
    check(cs.map_width == 3600, f"map width={cs.map_width}, expected 3600")
    check(cs.map_height == 2800, f"map height={cs.map_height}, expected 2800")
    check(close_pair(cs.world_to_svg(0, 0), (1800, 1400)), "world origin engineering mapping mismatch")
    check(close_pair(cs.world_to_svg(0, 0, "presentation"), (2100, 1600)), "world origin presentation mapping mismatch")

    known = {x["id"]: x for x in cfg["knownPointChecks"]}
    entrance_world = {x["id"]: (x["position"]["x"], x["position"]["z"]) for x in core["entrances"]}
    for pid, item in known.items():
        world = tuple(item["worldXZ"])
        if pid != "WORLD-ORIGIN":
            check(pid in entrance_world, f"known point {pid} missing from core entrances")
            if pid in entrance_world:
                check(world == entrance_world[pid], f"known point {pid} world coordinate differs from core data")
        eng = cs.world_to_svg(*world, profile="engineering")
        pre = cs.world_to_svg(*world, profile="presentation")
        check(close_pair(eng, tuple(item["engineeringSvgXY"])), f"{pid} engineering SVG mismatch: {eng}")
        check(close_pair(pre, tuple(item["presentationSvgXY"])), f"{pid} presentation SVG mismatch: {pre}")
        back = cs.svg_to_world(*eng, profile="engineering")
        check(close_pair(back, world, cs.round_trip_tolerance_m), f"{pid} round-trip mismatch: {back} != {world}")

    # Direction sanity: north must move upward on screen; east must move right.
    origin = cs.world_to_svg(0, 0)
    north = cs.world_to_svg(0, 100)
    east = cs.world_to_svg(100, 0)
    check(north[1] < origin[1] and north[0] == origin[0], "north is not SVG-up")
    check(east[0] > origin[0] and east[1] == origin[1], "east is not SVG-right")

    # Rotation contract: frozen campus facing convention.
    for deg in (0, 90, 180, 270):
        check(cs.world_rotation_y_to_svg_degrees(deg) == deg, f"rotation {deg} changed")

    # External roads including half-width must fit inside the frozen engineering map frame.
    half_width = float(ext["roadWidthMeters"]) / 2.0
    all_points = [p for road in ext["roads"] for p in road["centerlineXZ"]]
    min_x = min(p[0] for p in all_points)
    max_x = max(p[0] for p in all_points)
    min_z = min(p[1] for p in all_points)
    max_z = max(p[1] for p in all_points)
    check(min_x - half_width >= cs.x_min, "west external road stroke exceeds frozen frame")
    check(max_x + half_width <= cs.x_max, "east external road stroke exceeds frozen frame")
    check(min_z - half_width >= cs.z_min, "south external road stroke exceeds frozen frame")
    check(max_z + half_width <= cs.z_max, "north external road stroke exceeds frozen frame")

    expected_extents = cfg["extentAudit"]["currentExternalRoadCenterlineExtents"]
    check((min_x, max_x, min_z, max_z) == (
        expected_extents["xMin"], expected_extents["xMax"], expected_extents["zMin"], expected_extents["zMax"]
    ), "external road extents differ from coordinate config audit")

    # Campus legal boundary must fit the same frame exactly, with no coordinate clipping.
    for i, (x, z) in enumerate(core["campus"]["boundaryXZ"], start=1):
        check(cs.contains_world_point(x, z), f"campus boundary point {i} is outside frozen map frame")

    # A 500m semantic scale bar must remain exactly 500 SVG units in both profiles.
    for profile in ("engineering", "presentation"):
        a = cs.world_to_svg(-250, 0, profile)
        b = cs.world_to_svg(250, 0, profile)
        check(math.isclose(b[0] - a[0], 500.0), f"{profile} scale bar is not 1 unit/m")
        check(math.isclose(a[1], b[1]), f"{profile} scale bar is not horizontal")

    print(f"PATCH={EXPECTED_PATCH}")
    print(f"ENGINEERING_VIEWBOX=0 0 {int(cs.map_width)} {int(cs.map_height)}")
    print("ENGINEERING_WORLD_ORIGIN=1800,1400")
    print("PRESENTATION_VIEWBOX=0 0 4200 3200")
    print("PRESENTATION_WORLD_ORIGIN=2100,1600")
    print(f"EXTERNAL_ROAD_CENTERLINE_EXTENTS={min_x},{max_x},{min_z},{max_z}")
    print(f"ROUND_TRIP_TOLERANCE_M={cs.round_trip_tolerance_m}")
    if errors:
        for error in errors:
            print("FAIL", error)
        print(f"RESULT=FAIL errors={len(errors)}")
        return 1
    print("RESULT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

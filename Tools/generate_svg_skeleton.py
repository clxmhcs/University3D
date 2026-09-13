#!/usr/bin/env python3
"""Generate Step-3 Jiangcheng University SVG skeleton from frozen R6 data.

Inputs are authoritative data files. No campus geometry is duplicated here.
Outputs are deterministic vector SVGs for engineering review and Figma presentation.
"""
from __future__ import annotations

import json
import math
from html import escape
from pathlib import Path

from svg_coordinates import SvgCoordinateSystem, format_svg_number, svg_points_attribute

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "CampusData/svg/core_geometry_r6.json"
ROADS = ROOT / "CampusData/transport/external_roads.json"
WALL = ROOT / "CampusData/landscape/perimeter_wall.json"
COORD = ROOT / "CampusData/svg/svg_coordinate_system_r6.json"
OUT = ROOT / "Artifacts/SVG"
PATCH = "PATCH-2026-09-13-R6"

DISPLAY_NAMES = {
    "GATE-SOUTH": "江城大学南门",
    "GATE-WEST": "江城大学西门",
    "GATE-NORTH": "江城大学北门",
    "GATE-EAST": "江城大学东门",
    "GATE-SERVICE-SE": "东南后勤门",
    "ENT-HSP-SOCIAL": "附属医院社会入口",
    "ENT-HSP-EMERGENCY-CITY": "医院急救专用入口",
    "ENT-THEATER-PUBLIC": "戏剧表演中心社会入口",
    "ENT-RDI-VISITOR": "科研科技园访客入口",
}

ROAD_LABELS = {
    "ROAD-CITY-SOUTH": ((150, -1182), 0),
    "ROAD-CITY-NORTH": ((120, 1217), 0),
    "ROAD-CITY-WEST": ((-1653, -10), -90),
    "ROAD-CITY-EAST": ((1660, -10), 90),
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def cum_lengths(points):
    out = [0.0]
    for a, b in zip(points, points[1:]):
        out.append(out[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return out


def project_point_to_polyline(point, points):
    px, pz = point
    cumulative = cum_lengths(points)
    best = None
    for i, (a, b) in enumerate(zip(points, points[1:])):
        ax, az = a
        bx, bz = b
        vx, vz = bx - ax, bz - az
        length2 = vx * vx + vz * vz
        t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((px - ax) * vx + (pz - az) * vz) / length2))
        q = (ax + t * vx, az + t * vz)
        distance = math.hypot(px - q[0], pz - q[1])
        along = cumulative[i] + t * math.sqrt(length2)
        candidate = (distance, along, q)
        if best is None or candidate[0] < best[0]:
            best = candidate
    return best


def point_at_distance(points, distance):
    cumulative = cum_lengths(points)
    distance = max(0.0, min(cumulative[-1], distance))
    for i in range(len(points) - 1):
        if distance <= cumulative[i + 1] + 1e-9:
            segment = cumulative[i + 1] - cumulative[i]
            t = 0.0 if segment == 0 else (distance - cumulative[i]) / segment
            a, b = points[i], points[i + 1]
            return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
    return tuple(points[-1])


def slice_polyline(points, start, end):
    cumulative = cum_lengths(points)
    start = max(0.0, min(cumulative[-1], start))
    end = max(0.0, min(cumulative[-1], end))
    if end <= start + 1e-9:
        return []
    result = [point_at_distance(points, start)]
    for i in range(1, len(points) - 1):
        if start < cumulative[i] < end:
            result.append(tuple(points[i]))
    result.append(point_at_distance(points, end))
    return result


def assign_openings(wall_segments, openings, entrances):
    assignments = {}
    for opening in openings:
        target = opening["targetID"]
        p = entrances[target]
        best = None
        for wall in wall_segments:
            projection = project_point_to_polyline(p, wall["centerlineXZ"])
            candidate = (*projection, wall["id"])
            if best is None or candidate[0] < best[0]:
                best = candidate
        assignments[target] = best
    return assignments


def visible_wall_parts(wall, openings, assignments):
    points = wall["centerlineXZ"]
    total = cum_lengths(points)[-1]
    gaps = []
    for opening in openings:
        target = opening["targetID"]
        assignment = assignments[target]
        if assignment[-1] != wall["id"]:
            continue
        along = assignment[1]
        half = float(opening["clearWidthMeters"]) / 2.0
        gaps.append((max(0.0, along - half), min(total, along + half)))
    gaps.sort()
    merged = []
    for start, end in gaps:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    visible = []
    cursor = 0.0
    for start, end in merged:
        if start > cursor:
            visible.append(slice_polyline(points, cursor, start))
        cursor = end
    if cursor < total:
        visible.append(slice_polyline(points, cursor, total))
    return visible


def gate_label_offset(target):
    if target == "GATE-EAST":
        return (-180, -14)
    if target == "GATE-SOUTH":
        return (14, 30)
    if target == "GATE-NORTH":
        return (14, -18)
    return (14, -14)


def render(profile: str, core, roads, wall, cfg, cs: SvgCoordinateSystem):
    is_presentation = profile == "presentation"
    view_box = cfg["profiles"][profile]["documentViewBox"]
    width, height = view_box[2], view_box[3]
    road_width = float(roads["roadWidthMeters"])
    entrances = {
        e["id"]: (e["position"]["x"], e["position"]["z"])
        for e in core["entrances"]
    }
    openings = wall["openings"]
    opening_by_target = {o["targetID"]: o for o in openings}
    assignments = assign_openings(wall["segments"], openings, entrances)

    def w2s(point):
        return cs.world_to_svg(point[0], point[1], profile)

    def points(points_xz):
        return svg_points_attribute(cs.world_points_to_svg(points_xz, profile))

    def f(value):
        return format_svg_number(value)

    out = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">江城大学总平面骨架 R6 — Step 3</title>
  <desc id="desc">R6外围城市道路、6.513平方公里校园边界、校园围墙、校门和社会接口。世界坐标X向东、Z向北；1米等于1 SVG user unit。</desc>
  <metadata>sourcePatchVersion={PATCH}; generator=Tools/generate_svg_skeleton.py; profile={profile}; coordinateConfig=CampusData/svg/svg_coordinate_system_r6.json; noRaster=true</metadata>
  <defs>
    <style>
      .city-road {{ fill: none; stroke: #55585c; stroke-width: {f(road_width)}; stroke-linecap: round; stroke-linejoin: round; }}
      .city-road-center {{ fill: none; stroke: #f5f3ee; stroke-width: 1.5; stroke-dasharray: 18 14; opacity: .7; }}
      .campus-fill {{ fill: #f4f1e8; stroke: #8e948e; stroke-width: 3; stroke-linejoin: round; }}
      .wall {{ fill: none; stroke: #41464b; stroke-width: 5; stroke-linecap: butt; stroke-linejoin: round; }}
      .access {{ fill: none; stroke: #7f8589; stroke-width: 8; stroke-linecap: round; }}
      .gate {{ fill: #173A5E; stroke: #f4f1e8; stroke-width: 3; }}
      .gate-public {{ fill: #C4A052; stroke: #f4f1e8; stroke-width: 3; }}
      .technical {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK SC", sans-serif; font-size: 18px; fill: #2d3237; }}
      .road-name {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK SC", sans-serif; font-size: 28px; font-weight: 600; fill: #30353a; letter-spacing: 2px; }}
      .gate-name {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK SC", sans-serif; font-size: 18px; font-weight: 600; fill: #173A5E; }}
      .title {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK SC", sans-serif; font-size: 42px; font-weight: 700; fill: #173A5E; }}
      .subtitle {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK SC", sans-serif; font-size: 19px; fill: #5a6065; }}
      .legend {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK SC", sans-serif; font-size: 16px; fill: #3e4449; }}
    </style>
  </defs>''']

    if is_presentation:
        out += [
            '  <rect id="CanvasBackground" x="0" y="0" width="4200" height="3200" fill="#fbfaf6"/>',
            '  <text class="title" x="300" y="92">江城大学 · 总平面骨架</text>',
            '  <text class="subtitle" x="300" y="126">PATCH-2026-09-13-R6 · Step 3 · 外围道路 / 校园边界 / 围墙 / 校门</text>',
        ]

    out.append('  <g id="01_CityRoads" data-layer="city-roads">')
    for road in roads["roads"]:
        p = points(road["centerlineXZ"])
        out.append(f'    <polyline id="{road["id"]}" class="city-road" points="{p}" data-width-m="{f(road_width)}"/>')
        out.append(f'    <polyline id="{road["id"]}-CENTER" class="city-road-center" points="{p}"/>')
    out.append('  </g>')

    out.append('  <g id="02_CampusBoundary" data-layer="campus-boundary">')
    out.append(f'    <polygon id="CAMPUS-01-BOUNDARY" class="campus-fill" points="{points(core["campus"]["boundaryXZ"])}" data-area-km2="6.513"/>')
    out.append('  </g>')

    out.append('  <g id="03_PerimeterWall" data-layer="perimeter-wall">')
    for segment in wall["segments"]:
        for index, visible in enumerate(visible_wall_parts(segment, openings, assignments), 1):
            out.append(f'    <polyline id="{segment["id"]}-PART-{index:02d}" class="wall" points="{points(visible)}" data-source-wall="{segment["id"]}"/>')
    out.append('  </g>')

    out.append('  <g id="04_Gates" data-layer="gates-and-social-interfaces">')
    for target in [o["targetID"] for o in openings]:
        world = entrances[target]
        projected = assignments[target][2]
        p = w2s(world)
        q = w2s(projected)
        clear_width = opening_by_target[target]["clearWidthMeters"]
        out.append(f'    <line id="ACCESS-{target}" class="access" x1="{f(p[0])}" y1="{f(p[1])}" x2="{f(q[0])}" y2="{f(q[1])}" data-opening-target="{target}" data-clear-width-m="{f(clear_width)}"/>')
        css = "gate" if target.startswith("GATE-") else "gate-public"
        out.append(f'    <circle id="{target}" class="{css}" cx="{f(p[0])}" cy="{f(p[1])}" r="10" data-world-x="{world[0]}" data-world-z="{world[1]}"/>')
        dx, dy = gate_label_offset(target)
        out.append(f'    <text class="gate-name" x="{f(p[0] + dx)}" y="{f(p[1] + dy)}">{escape(DISPLAY_NAMES[target])}</text>')
    out.append('  </g>')

    for group_id in ["05_InternalRoads", "06_Water", "07_Landscape", "08_Buildings", "09_Residential", "10_Sports", "11_POI", "12_Labels"]:
        out.append(f'  <g id="{group_id}" data-step="future"/>')

    out.append('  <g id="13_RoadNames" data-layer="road-names">')
    for road in roads["roads"]:
        label_world, rotation = ROAD_LABELS[road["id"]]
        p = w2s(label_world)
        out.append(f'    <text class="road-name" x="{f(p[0])}" y="{f(p[1])}" text-anchor="middle" transform="rotate({rotation} {f(p[0])} {f(p[1])})">{escape(road["name"])}</text>')
    out.append('  </g>')

    out.append('  <g id="14_Legend" data-layer="legend">')
    if is_presentation:
        out += [
            '    <text class="legend" x="3530" y="230">N</text>',
            '    <path d="M 3538 244 L 3538 324 M 3525 262 L 3538 244 L 3551 262" fill="none" stroke="#173A5E" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>',
            '    <line x1="3250" y1="3040" x2="3750" y2="3040" stroke="#30353a" stroke-width="6"/>',
            '    <line x1="3250" y1="3028" x2="3250" y2="3052" stroke="#30353a" stroke-width="4"/>',
            '    <line x1="3750" y1="3028" x2="3750" y2="3052" stroke="#30353a" stroke-width="4"/>',
            '    <text class="legend" x="3250" y="3018">0</text>',
            '    <text class="legend" x="3750" y="3018" text-anchor="end">500 m</text>',
        ]
    else:
        out += [
            '    <text class="technical" x="88" y="82">N</text>',
            '    <path d="M 88 100 L 88 180 M 75 118 L 88 100 L 101 118" fill="none" stroke="#173A5E" stroke-width="5"/>',
            '    <line x1="2920" y1="2700" x2="3420" y2="2700" stroke="#30353a" stroke-width="6"/>',
            '    <text class="technical" x="2920" y="2682">500 m</text>',
        ]
    out.append('  </g>')
    out.append('</svg>')
    return "\n".join(out) + "\n"


def main():
    core = load_json(CORE)
    roads = load_json(ROADS)
    wall = load_json(WALL)
    cfg = load_json(COORD)
    for source in (core, roads, wall, cfg):
        if source.get("sourcePatchVersion") != PATCH:
            raise SystemExit(f"source patch mismatch: {source.get('sourcePatchVersion')}")
    cs = SvgCoordinateSystem.from_file(COORD)
    OUT.mkdir(parents=True, exist_ok=True)
    outputs = {
        "engineering": OUT / "Jiangcheng-University-MasterPlan-Skeleton-R6-Engineering.svg",
        "presentation": OUT / "Jiangcheng-University-MasterPlan-Skeleton-R6-Figma.svg",
    }
    for profile, path in outputs.items():
        path.write_text(render(profile, core, roads, wall, cfg, cs), encoding="utf-8")
        print(f"WROTE {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

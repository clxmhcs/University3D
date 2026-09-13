#!/usr/bin/env python3
"""Generate Step-4 Jiangcheng University masterplan SVG from frozen R6/R3 data.

Step 4 extends the Step-3 perimeter skeleton with:
- current valid internal roads / transit geometry;
- Chenghu exact shoreline and R6 water system;
- major squares and source-supported open-space geometry.

No hand-authored campus coordinates are allowed in this generator. Geometry comes from
CampusData; presentation-only labels/markers are derived at render time.
"""
from __future__ import annotations

import json
import math
from html import escape
from pathlib import Path

from svg_coordinates import SvgCoordinateSystem, format_svg_number, svg_points_attribute
from generate_svg_skeleton import assign_openings, visible_wall_parts, gate_label_offset, DISPLAY_NAMES, ROAD_LABELS

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "CampusData/svg/core_geometry_r6.json"
CITY_ROADS = ROOT / "CampusData/transport/external_roads.json"
WALL = ROOT / "CampusData/landscape/perimeter_wall.json"
INTERNAL = ROOT / "CampusData/svg/internal_roads_r3.json"
WATER = ROOT / "CampusData/svg/water_r6.json"
COORD = ROOT / "CampusData/svg/svg_coordinate_system_r6.json"
OUT = ROOT / "Artifacts/SVG"
PATCH = "PATCH-2026-09-13-R6"

OUTPUTS = {
    "engineering": OUT / "Jiangcheng-University-MasterPlan-Step4-R6-Engineering.svg",
    "presentation": OUT / "Jiangcheng-University-MasterPlan-Step4-R6-Figma.svg",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def signed_area(points):
    a = 0.0
    for p, q in zip(points, points[1:] + points[:1]):
        a += p[0] * q[1] - q[0] * p[1]
    return a / 2.0


def line_intersection(p1, d1, p2, d2):
    cross = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(cross) < 1e-9:
        return None
    rx, rz = p2[0] - p1[0], p2[1] - p1[1]
    t = (rx * d2[1] - rz * d2[0]) / cross
    return (p1[0] + t * d1[0], p1[1] + t * d1[1])


def offset_closed_polygon(points, distance):
    """Miter-offset a simple closed XZ polygon by `distance` meters outward."""
    pts = [tuple(map(float, p)) for p in points]
    ccw = signed_area(pts) > 0
    shifted = []
    for a, b in zip(pts, pts[1:] + pts[:1]):
        dx, dz = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dz)
        if length == 0:
            raise ValueError("zero-length shoreline segment")
        # For CCW polygons interior is left; outward is right.
        nx, nz = ((dz / length, -dx / length) if ccw else (-dz / length, dx / length))
        shifted.append(((a[0] + nx * distance, a[1] + nz * distance), (dx, dz)))
    out = []
    for i in range(len(pts)):
        prev_p, prev_d = shifted[i - 1]
        cur_p, cur_d = shifted[i]
        q = line_intersection(prev_p, prev_d, cur_p, cur_d)
        if q is None:
            # Parallel fallback: use current shifted vertex, still data-derived.
            q = cur_p
        out.append(q)
    return out


def polyline_midpoint(points):
    lengths = []
    total = 0.0
    for a, b in zip(points, points[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        lengths.append(seg)
        total += seg
    if total == 0:
        return tuple(points[0]), 0.0
    target = total / 2.0
    acc = 0.0
    for i, seg in enumerate(lengths):
        if acc + seg >= target:
            t = (target - acc) / seg
            a, b = points[i], points[i + 1]
            x = a[0] + t * (b[0] - a[0])
            z = a[1] + t * (b[1] - a[1])
            angle_world = math.degrees(math.atan2(b[0] - a[0], b[1] - a[1]))
            # Keep text upright.
            angle_svg = angle_world
            if 90 < angle_svg <= 270:
                angle_svg -= 180
            elif -270 <= angle_svg < -90:
                angle_svg += 180
            return (x, z), angle_svg
        acc += seg
    return tuple(points[-1]), 0.0


def circle_radius_from_area(area_m2):
    return math.sqrt(float(area_m2) / math.pi)


def road_css(road_class):
    return {
        "primary": "internal-road primary-road",
        "secondary": "internal-road secondary-road",
        "tertiary": "internal-road tertiary-road",
        "emergency": "internal-road emergency-road",
        "event_access": "internal-road event-road",
        "transit_only": "internal-road transit-road",
        "ped_bike": "internal-road pedbike-road",
    }.get(road_class, "internal-road tertiary-road")


def render(profile, core, city_roads, wall, internal, water, cfg, cs):
    is_presentation = profile == "presentation"
    view_box = cfg["profiles"][profile]["documentViewBox"]
    width, height = view_box[2], view_box[3]
    road_width = float(city_roads["roadWidthMeters"])
    entrances = {e["id"]: (e["position"]["x"], e["position"]["z"]) for e in core["entrances"]}
    openings = wall["openings"]
    opening_by_target = {o["targetID"]: o for o in openings}
    assignments = assign_openings(wall["segments"], openings, entrances)
    chenghu = next(w for w in water["waterBodies"] if w["id"] == "WATER-LAKE-01")
    chenghu_path = offset_closed_polygon(chenghu["shorelineXZ"], 25.0)

    def w2s(point):
        return cs.world_to_svg(point[0], point[1], profile)

    def pts(points_xz):
        return svg_points_attribute(cs.world_points_to_svg(points_xz, profile))

    def f(value):
        return format_svg_number(value)

    out = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">江城大学总平面 R6 — Step 4</title>
  <desc id="desc">R6外围骨架、R3当前有效内部道路、澄湖与R6水系、主要广场和开放空间。1米等于1 SVG user unit。</desc>
  <metadata>sourcePatchVersion={PATCH}; generator=Tools/generate_svg_step4.py; profile={profile}; step=4; coordinateConfig=CampusData/svg/svg_coordinate_system_r6.json; noRaster=true</metadata>
  <defs>
    <style>
      .city-road {{ fill:none; stroke:#55585c; stroke-width:{f(road_width)}; stroke-linecap:round; stroke-linejoin:round; }}
      .city-road-center {{ fill:none; stroke:#f5f3ee; stroke-width:1.5; stroke-dasharray:18 14; opacity:.7; }}
      .campus-fill {{ fill:#f4f1e8; stroke:#8e948e; stroke-width:3; stroke-linejoin:round; }}
      .wall {{ fill:none; stroke:#41464b; stroke-width:5; stroke-linecap:butt; stroke-linejoin:round; }}
      .access {{ fill:none; stroke:#7f8589; stroke-width:8; stroke-linecap:round; }}
      .gate {{ fill:#173A5E; stroke:#f4f1e8; stroke-width:3; }}
      .gate-public {{ fill:#C4A052; stroke:#f4f1e8; stroke-width:3; }}
      .internal-road {{ fill:none; stroke-linecap:round; stroke-linejoin:round; }}
      .primary-road {{ stroke:#757b80; }}
      .secondary-road {{ stroke:#93989c; }}
      .tertiary-road {{ stroke:#b1b5b8; }}
      .emergency-road {{ stroke:#a56b62; }}
      .event-road {{ stroke:#848c91; }}
      .transit-road {{ stroke:#607f91; stroke-dasharray:15 9; }}
      .pedbike-road {{ stroke:#6f8b72; stroke-dasharray:10 7; }}
      .road-center {{ fill:none; stroke:#fffdf8; stroke-width:1.2; opacity:.58; stroke-dasharray:12 10; }}
      .water-main {{ fill:#b7d9e8; stroke:#6f9fb5; stroke-width:3; }}
      .water-reference {{ fill:#c7e1eb; fill-opacity:.72; stroke:#78a9bc; stroke-width:2; stroke-dasharray:8 6; }}
      .stream {{ fill:none; stroke:#79abc0; stroke-width:10; stroke-linecap:round; stroke-linejoin:round; }}
      .stream-center {{ fill:none; stroke:#d9eef6; stroke-width:2; stroke-linecap:round; }}
      .island-marker {{ fill:#7d9a72; stroke:#f4f1e8; stroke-width:2; }}
      .square-marker {{ fill:#d9d1bf; fill-opacity:.65; stroke:#8f8778; stroke-width:2; }}
      .park-reference {{ fill:#cbdcc5; fill-opacity:.32; stroke:#78906f; stroke-width:2; stroke-dasharray:10 7; }}
      .lawn-envelope {{ fill:#dce8cf; fill-opacity:.5; stroke:#80956f; stroke-width:2; stroke-dasharray:12 7; }}
      .seasonal-path {{ fill:none; stroke:#9aaf7d; stroke-width:5; stroke-dasharray:10 8; stroke-linecap:round; }}
      .bus-stop {{ fill:#173A5E; stroke:#f4f1e8; stroke-width:1.5; }}
      .junction {{ fill:#faf8f1; stroke:#6c7378; stroke-width:1.5; }}
      .technical {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:18px; fill:#2d3237; }}
      .road-name {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:24px; font-weight:600; fill:#4d555a; letter-spacing:1px; }}
      .city-road-name {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:28px; font-weight:600; fill:#30353a; letter-spacing:2px; }}
      .gate-name {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:18px; font-weight:600; fill:#173A5E; }}
      .water-name {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:20px; font-weight:600; fill:#416f83; }}
      .open-name {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:17px; font-weight:600; fill:#596b52; }}
      .small-name {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:14px; fill:#566168; }}
      .title {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:42px; font-weight:700; fill:#173A5E; }}
      .subtitle {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:19px; fill:#5a6065; }}
      .legend {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:16px; fill:#3e4449; }}
    </style>
  </defs>''']

    if is_presentation:
        out += [
            '  <rect id="CanvasBackground" x="0" y="0" width="4200" height="3200" fill="#fbfaf6"/>',
            '  <text class="title" x="300" y="92">江城大学 · 总平面</text>',
            '  <text class="subtitle" x="300" y="126">PATCH-2026-09-13-R6 · Step 4 · 内部道路 / 水系 / 广场 / 开放空间</text>',
        ]

    out.append('  <g id="01_CityRoads" data-layer="city-roads">')
    for road in city_roads["roads"]:
        p = pts(road["centerlineXZ"])
        out.append(f'    <polyline id="{road["id"]}" class="city-road" points="{p}" data-width-m="{f(road_width)}"/>')
        out.append(f'    <polyline id="{road["id"]}-CENTER" class="city-road-center" points="{p}"/>')
    out.append('  </g>')

    out.append('  <g id="02_CampusBoundary" data-layer="campus-boundary">')
    out.append(f'    <polygon id="CAMPUS-01-BOUNDARY" class="campus-fill" points="{pts(core["campus"]["boundaryXZ"])}" data-area-km2="6.513"/>')
    out.append('  </g>')

    out.append('  <g id="03_PerimeterWall" data-layer="perimeter-wall">')
    for segment in wall["segments"]:
        for index, visible in enumerate(visible_wall_parts(segment, openings, assignments), 1):
            out.append(f'    <polyline id="{segment["id"]}-PART-{index:02d}" class="wall" points="{pts(visible)}" data-source-wall="{segment["id"]}"/>')
    out.append('  </g>')

    out.append('  <g id="04_Gates" data-layer="gates-and-social-interfaces">')
    for target in [o["targetID"] for o in openings]:
        world = entrances[target]
        projected = assignments[target][2]
        p, q = w2s(world), w2s(projected)
        clear_width = opening_by_target[target]["clearWidthMeters"]
        out.append(f'    <line id="ACCESS-{target}" class="access" x1="{f(p[0])}" y1="{f(p[1])}" x2="{f(q[0])}" y2="{f(q[1])}" data-opening-target="{target}" data-clear-width-m="{f(clear_width)}"/>')
        css = "gate" if target.startswith("GATE-") else "gate-public"
        out.append(f'    <circle id="{target}" class="{css}" cx="{f(p[0])}" cy="{f(p[1])}" r="10" data-world-x="{world[0]}" data-world-z="{world[1]}"/>')
        dx, dy = gate_label_offset(target)
        out.append(f'    <text class="gate-name" x="{f(p[0]+dx)}" y="{f(p[1]+dy)}">{escape(DISPLAY_NAMES[target])}</text>')
    out.append('  </g>')

    out.append('  <g id="05_InternalRoads" data-layer="internal-roads">')
    for road in internal["internalRoads"]:
        if road["id"] == "PATH-CHENGHU":
            centerline = chenghu_path + [chenghu_path[0]]
            geometry_source = "derived:WATER-LAKE-01 shoreline outward 25m"
        else:
            centerline = road["centerlineXZ"]
            geometry_source = "source:centerlineXZ"
        css = road_css(road["class"])
        width_m = float(road["width"])
        p = pts(centerline)
        out.append(f'    <polyline id="{road["id"]}" class="{css}" points="{p}" stroke-width="{f(width_m)}" data-class="{road["class"]}" data-width-m="{f(width_m)}" data-geometry-source="{escape(geometry_source)}"/>')
        if road["class"] not in ("ped_bike", "transit_only"):
            out.append(f'    <polyline id="{road["id"]}-CENTER" class="road-center" points="{p}"/>')
    for stop in internal["busStops"]:
        p = w2s(stop["positionXZ"])
        out.append(f'    <circle id="{stop["id"]}" class="bus-stop" cx="{f(p[0])}" cy="{f(p[1])}" r="5" data-lines="{",".join(stop["lines"])}"/>')
    for jct in internal["junctions"]:
        p = w2s(jct["positionXZ"])
        out.append(f'    <circle id="{jct["id"]}" class="junction" cx="{f(p[0])}" cy="{f(p[1])}" r="3.5"/>')
    out.append('  </g>')

    out.append('  <g id="06_Water" data-layer="water">')
    out.append(f'    <polygon id="WATER-LAKE-01" class="water-main" points="{pts(chenghu["shorelineXZ"])}" data-water-level-y="{f(chenghu["waterLevelY"])}" data-area-m2="{chenghu["areaApproxM2"]}" data-geometry="exact-shoreline"/>')
    island = w2s(chenghu["mainIslandCenterXZ"])
    out.append(f'    <circle id="WATER-LAKE-01-MAIN-ISLAND-CENTER" class="island-marker" cx="{f(island[0])}" cy="{f(island[1])}" r="6" data-area-ha-range="0.6-0.8" data-geometry="center-marker-only"/>')
    for body in water["waterBodies"]:
        if body["id"] == "WATER-LAKE-01":
            continue
        p = w2s(body["centerXZ"])
        r = circle_radius_from_area(body["areaApproxM2"])
        out.append(f'    <circle id="{body["id"]}" class="water-reference" cx="{f(p[0])}" cy="{f(p[1])}" r="{f(r)}" data-area-m2="{body["areaApproxM2"]}" data-water-level-y="{f(body["waterLevelY"])}" data-geometry="area-equivalent-reference-circle"/>')
    stream = water["mainStream"]
    for suffix, chain in (("NORTH", stream["northInflowXZ"]), ("SOUTHEAST", stream["southeastOutflowXZ"])):
        p = pts(chain)
        out.append(f'    <polyline id="{stream["id"]}-{suffix}" class="stream" points="{p}" data-visible-length-km="{stream["visibleLengthApproxKm"]}"/>')
        out.append(f'    <polyline id="{stream["id"]}-{suffix}-CENTER" class="stream-center" points="{p}"/>')
    out.append('  </g>')

    out.append('  <g id="07_Landscape" data-layer="major-open-space">')
    for i, sq in enumerate(core["squares"], 1):
        p = w2s(sq["centerXZ"])
        out.append(f'    <rect id="SQUARE-{i:02d}" class="square-marker" x="{f(p[0]-8)}" y="{f(p[1]-8)}" width="16" height="16" transform="rotate(45 {f(p[0])} {f(p[1])})" data-name="{escape(sq["name"])}" data-geometry="center-marker-only"/>')
    for i, park in enumerate(core["parks"], 1):
        if "areaHa" in park:
            p = w2s(park["centerXZ"])
            radius = circle_radius_from_area(float(park["areaHa"]) * 10000.0)
            out.append(f'    <circle id="PARK-{i:02d}" class="park-reference" cx="{f(p[0])}" cy="{f(p[1])}" r="{f(radius)}" data-name="{escape(park["name"])}" data-area-ha="{park["areaHa"]}" data-geometry="area-equivalent-reference-circle"/>')
        else:
            xr, zr = park["range"]["x"], park["range"]["z"]
            a, b = w2s((xr[0], zr[1])), w2s((xr[1], zr[0]))
            out.append(f'    <rect id="PARK-{i:02d}" class="park-reference" x="{f(a[0])}" y="{f(a[1])}" width="{f(b[0]-a[0])}" height="{f(b[1]-a[1])}" data-name="{escape(park["name"])}" data-geometry="source-control-range"/>')
    lawn = core["centralLawn"]
    a = w2s((lawn["xRange"][0], lawn["zRange"][1]))
    b = w2s((lawn["xRange"][1], lawn["zRange"][0]))
    out.append(f'    <rect id="{lawn["id"]}" class="lawn-envelope" x="{f(a[0])}" y="{f(a[1])}" width="{f(b[0]-a[0])}" height="{f(b[1]-a[1])}" data-area-ha-range="{lawn["areaHaApprox"][0]}-{lawn["areaHaApprox"][1]}" data-geometry="source-control-envelope"/>')
    for path in core.get("seasonalPaths", []):
        out.append(f'    <polyline id="{path["id"]}" class="seasonal-path" points="{pts(path["centerlineXZ"])}" data-name="{escape(path["name"])}" data-alias="{escape(path["alias"])}"/>')
    out.append('  </g>')

    for group_id in ["08_Buildings", "09_Residential", "10_Sports", "11_POI"]:
        out.append(f'  <g id="{group_id}" data-step="future"/>')

    out.append('  <g id="12_Labels" data-layer="step4-labels">')
    # Water labels: exact center/defined center only.
    for body in water["waterBodies"]:
        p = w2s(body["centerXZ"])
        out.append(f'    <text class="water-name" x="{f(p[0])}" y="{f(p[1]-12)}" text-anchor="middle">{escape(body["name"])}</text>')
    for sq in core["squares"]:
        p = w2s(sq["centerXZ"])
        out.append(f'    <text class="small-name" x="{f(p[0]+12)}" y="{f(p[1]-10)}">{escape(sq["name"])}</text>')
    for park in core["parks"]:
        if "centerXZ" in park:
            p = w2s(park["centerXZ"])
        else:
            p = w2s(((park["range"]["x"][0]+park["range"]["x"][1])/2, (park["range"]["z"][0]+park["range"]["z"][1])/2))
        out.append(f'    <text class="open-name" x="{f(p[0])}" y="{f(p[1])}" text-anchor="middle">{escape(park["name"])}</text>')
    lp = w2s(((lawn["xRange"][0]+lawn["xRange"][1])/2, (lawn["zRange"][0]+lawn["zRange"][1])/2))
    out.append(f'    <text class="open-name" x="{f(lp[0])}" y="{f(lp[1])}" text-anchor="middle">{escape(lawn["name"])}</text>')
    out.append('  </g>')

    out.append('  <g id="13_RoadNames" data-layer="road-names">')
    for road in city_roads["roads"]:
        label_world, rotation = ROAD_LABELS[road["id"]]
        p = w2s(label_world)
        out.append(f'    <text class="city-road-name" x="{f(p[0])}" y="{f(p[1])}" text-anchor="middle" transform="rotate({rotation} {f(p[0])} {f(p[1])})">{escape(road["name"])}</text>')
    for road in internal["internalRoads"]:
        if road["id"] == "PATH-CHENGHU":
            centerline = chenghu_path + [chenghu_path[0]]
        else:
            centerline = road["centerlineXZ"]
        # Connectors/feeders/transit-only remain visible but do not all receive text to limit clutter.
        if any(token in road["id"] for token in ("-FEED", "-CONNECT")) or road["class"] == "transit_only":
            continue
        midpoint, rotation = polyline_midpoint(centerline)
        p = w2s(midpoint)
        out.append(f'    <text class="road-name" x="{f(p[0])}" y="{f(p[1]-8)}" text-anchor="middle" transform="rotate({f(rotation)} {f(p[0])} {f(p[1]-8)})">{escape(road["name"])}</text>')
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
            '    <text class="legend" x="300" y="3130">虚线圆形水体/公园 = 依据已冻结中心与面积生成的等面积参考轮廓，不代表最终岸线/边界。</text>',
        ]
    else:
        out += [
            '    <text class="technical" x="88" y="82">N</text>',
            '    <path d="M 88 100 L 88 180 M 75 118 L 88 100 L 101 118" fill="none" stroke="#173A5E" stroke-width="5"/>',
            '    <line x1="2920" y1="2700" x2="3420" y2="2700" stroke="#30353a" stroke-width="6"/>',
            '    <text class="technical" x="2920" y="2682">500 m</text>',
            '    <text class="technical" x="80" y="2740">Reference circles derive from source center + area; only 澄湖 has exact shoreline in Step 4.</text>',
        ]
    out.append('  </g>')
    out.append('</svg>')
    return "\n".join(out) + "\n"


def main():
    core = load_json(CORE)
    city_roads = load_json(CITY_ROADS)
    wall = load_json(WALL)
    internal = load_json(INTERNAL)
    water = load_json(WATER)
    cfg = load_json(COORD)
    for source in (core, city_roads, wall, internal, water, cfg):
        if source.get("sourcePatchVersion") != PATCH:
            raise SystemExit(f"source patch mismatch: {source.get('sourcePatchVersion')}")
    cs = SvgCoordinateSystem.from_file(COORD)
    OUT.mkdir(parents=True, exist_ok=True)
    for profile, path in OUTPUTS.items():
        path.write_text(render(profile, core, city_roads, wall, internal, water, cfg, cs), encoding="utf-8")
        print(f"WROTE {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

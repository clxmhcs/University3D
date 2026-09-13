#!/usr/bin/env python3
"""Generate Step-6 Jiangcheng University masterplan SVG.

Step 6 is deliberately presentation-only on top of Step 5 engineering geometry.
It may:
- refine the muted architectural palette;
- add source-control district washes and labels;
- visualize the two landscape axes;
- visualize four 2-4 ha life-green-heart ranges using residence centroids;
- add data-derived cherry/ginkgo avenue symbols and riparian buffers.

It may NOT move, resize or rotate any Step-5 engineering object.
"""
from __future__ import annotations

import json
import math
from html import escape
from pathlib import Path

import generate_svg_step5 as step5
from svg_coordinates import SvgCoordinateSystem, format_svg_number, svg_points_attribute

ROOT = Path(__file__).resolve().parents[1]
VISUAL_POLICY = ROOT / "CampusData/svg/step6_visual_policy_r6.json"
OUT = ROOT / "Artifacts/SVG"
PATCH = "PATCH-2026-09-13-R6"

OUTPUTS = {
    "engineering": OUT / "Jiangcheng-University-MasterPlan-Step6-R6-Engineering.svg",
    "presentation": OUT / "Jiangcheng-University-MasterPlan-Step6-R6-Figma.svg",
}

MAJOR_LABEL_IDS = {
    "CEN-01": "博雅图书馆",
    "CEN-02": "行政中心",
    "CEN-03": "大学会堂",
    "ATH-01": "综合体育馆",
    "ART-03": "戏剧表演中心",
    "LAW-01": "法学院 / 法律援助",
    "HSP-01": "江城大学附属医院",
    "LIFE-C-01": "校园商业中心",
}

DISTRICT_TONES = [
    ("#8f9b8a", "#6f7c69"),
    ("#b09c87", "#856f5c"),
    ("#9a9c92", "#73766e"),
    ("#83969d", "#60747c"),
    ("#899797", "#627372"),
    ("#b0a58f", "#827763"),
]


def f(value):
    return format_svg_number(value)


def load_all():
    core = step5.load_json(step5.CORE)
    city_roads = step5.load_json(step5.CITY_ROADS)
    wall = step5.load_json(step5.WALL)
    internal = step5.load_json(step5.INTERNAL)
    water = step5.load_json(step5.WATER)
    cfg = step5.load_json(step5.COORD)
    sports = step5.load_json(step5.SPORTS)
    step5_policy = step5.load_json(step5.POLICY)
    visual_policy = step5.load_json(VISUAL_POLICY)
    rows = step5.load_csv(step5.BUILDINGS)
    for source in (core, city_roads, wall, internal, water, cfg, sports, step5_policy, visual_policy):
        if source.get("sourcePatchVersion") != PATCH:
            raise SystemExit(f"source patch mismatch: {source.get('sourcePatchVersion')}")
    return core, city_roads, wall, internal, water, cfg, sports, step5_policy, visual_policy, rows


def row_matches_group(row_id, group):
    if row_id in group.get("explicitIDs", []):
        return True
    return any(row_id.startswith(prefix) for prefix in group.get("prefixes", []))


def building_style_assignment(rows, visual_policy, step5_policy):
    routed = set(step5_policy["buildingTableSpecialRouting"]["sportsSurfaceIDs"]) | set(
        step5_policy["buildingTableSpecialRouting"]["sportsStandIDs"]
    )
    assignments = {}
    for row in rows:
        rid = row["id"]
        if rid.startswith("RES-") or rid in routed:
            continue
        matches = [
            name for name, group in visual_policy["buildingStyleGroups"].items()
            if row_matches_group(rid, group)
        ]
        if len(matches) != 1:
            raise ValueError(f"Step 6 building style assignment for {rid}: {matches}")
        assignments[rid] = matches[0]
    return assignments


def inject_visual_styles(svg, profile, rows, visual_policy, step5_policy):
    assignments = building_style_assignment(rows, visual_policy, step5_policy)
    rules = []
    for group_name, group in visual_policy["buildingStyleGroups"].items():
        ids = [rid for rid, assigned in assignments.items() if assigned == group_name]
        if not ids:
            continue
        selector = ",".join(f"#{rid}" for rid in ids)
        rules.append(
            f"      {selector} {{ fill:{group['fill']}; stroke:{group['stroke']}; }}"
        )

    # Four life areas retain the same material family but gain slight character shifts.
    residence_styles = {
        "RES-W-": ("#ddd8cf", "#756f66"),
        "RES-N-": ("#dfe1d7", "#70786c"),
        "RES-E-": ("#ddd2c8", "#7a675d"),
        "RES-S-": ("#e0d7c8", "#786d5e"),
    }
    for prefix, (fill, stroke) in residence_styles.items():
        ids = [r["id"] for r in rows if r["id"].startswith(prefix)]
        rules.append(f"      {','.join('#'+rid for rid in ids)} {{ fill:{fill}; stroke:{stroke}; }}")

    # Keep the hospital upper-tower overlay visually distinct despite the medical palette.
    rules += [
        "      #HSP-02 { fill:#c89e98; fill-opacity:.42; stroke:#7d4d47; stroke-width:3; stroke-dasharray:10 6; }",
        "      #CEN-01,#CEN-02,#CEN-03,#ATH-01,#ART-03,#LAW-01,#HSP-01 { stroke:#173A5E; stroke-width:3; }",
        "      #PARK-01 { fill:#c9d2c2; stroke:#71806c; }",
        "      #PARK-02 { fill:#d3dbc9; stroke:#78846f; }",
        "      #PARK-03 { fill:#cfdbc9; stroke:#71856e; }",
        "      #PARK-04 { fill:#d4d2c8; stroke:#817a70; }",
        "      #PARK-05 { fill:#c1d0bc; fill-opacity:.55; stroke:#667c62; }",
        "      #POI-BOYA-LAWN { fill:#dbe6cf; fill-opacity:.68; stroke:#80956f; }",
        "      .step6-district { stroke-width:2; stroke-dasharray:14 10; pointer-events:none; }",
        "      .step6-axis-ceremonial { fill:none; stroke:#173A5E; stroke-width:18; stroke-opacity:.12; stroke-linecap:round; stroke-linejoin:round; pointer-events:none; }",
        "      .step6-axis-eco { fill:none; stroke:#799071; stroke-width:24; stroke-opacity:.14; stroke-linecap:round; stroke-linejoin:round; pointer-events:none; }",
        "      .step6-greenheart-inner { fill:#cbdcbd; fill-opacity:.24; stroke:#78906f; stroke-width:2; pointer-events:none; }",
        "      .step6-greenheart-outer { fill:none; stroke:#78906f; stroke-opacity:.7; stroke-width:2; stroke-dasharray:9 7; pointer-events:none; }",
        "      .step6-riparian-lake { fill:none; stroke:#a8c89e; stroke-opacity:.42; stroke-linejoin:round; pointer-events:none; }",
        "      .step6-riparian-stream { fill:none; stroke:#afd0a6; stroke-opacity:.38; stroke-linecap:round; stroke-linejoin:round; pointer-events:none; }",
        "      .step6-tree-cherry { fill:#d9b9bd; stroke:#9f7f82; stroke-width:1; pointer-events:none; }",
        "      .step6-tree-ginkgo { fill:#C4A052; fill-opacity:.82; stroke:#8f7539; stroke-width:1; pointer-events:none; }",
        "      .step6-district-label { font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",\"Noto Sans CJK SC\",sans-serif; font-size:24px; font-weight:700; fill:#586068; fill-opacity:.82; letter-spacing:1px; pointer-events:none; }",
        "      .step6-life-label { font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",\"Noto Sans CJK SC\",sans-serif; font-size:25px; font-weight:800; fill:#173A5E; pointer-events:none; }",
        "      .step6-major-label { font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",\"Noto Sans CJK SC\",sans-serif; font-size:18px; font-weight:700; fill:#30383d; paint-order:stroke; stroke:#fbfaf6; stroke-width:5; stroke-linejoin:round; pointer-events:none; }",
        "      .step6-axis-label { font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",\"Noto Sans CJK SC\",sans-serif; font-size:17px; font-weight:700; fill:#627064; pointer-events:none; }",
        "      .step6-legend-title { font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",\"Noto Sans CJK SC\",sans-serif; font-size:17px; font-weight:700; fill:#173A5E; }",
        "      .step6-legend-note { font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",\"Noto Sans CJK SC\",sans-serif; font-size:14px; fill:#596167; }",
    ]
    if profile == "presentation":
        rules.append("      .building-id,.residence-id,.sport-id { display:none; }")
        rules.append("      .city-road { stroke:#626568; }")
        rules.append("      .campus-fill { fill:#f5f1e7; }")
    return svg.replace("    </style>", "\n".join(rules) + "\n    </style>", 1)


def world_rect_from_ranges(cs, profile, x_range, z_range):
    top_left = cs.world_to_svg(float(x_range[0]), float(z_range[1]), profile)
    bottom_right = cs.world_to_svg(float(x_range[1]), float(z_range[0]), profile)
    return top_left[0], top_left[1], bottom_right[0] - top_left[0], bottom_right[1] - top_left[1]


def district_group(core, cs, profile, visual_policy):
    if profile != "presentation":
        return '  <g id="15_DistrictIdentity" data-layer="district-identity" data-presentation="omitted-in-engineering"/>'
    fill_opacity = float(visual_policy["districtPresentation"]["fillOpacity"])
    stroke_opacity = float(visual_policy["districtPresentation"]["strokeOpacity"])
    out = ['  <g id="15_DistrictIdentity" data-layer="district-identity" data-geometry="reference-only">']
    rendered = 0
    for index, district in enumerate(core["districts"]):
        if "xRange" not in district or "zRange" not in district:
            continue
        x, y, width, height = world_rect_from_ranges(cs, profile, district["xRange"], district["zRange"])
        fill, stroke = DISTRICT_TONES[index % len(DISTRICT_TONES)]
        out.append(
            f'    <rect id="STEP6-{district["id"]}" class="step6-district" x="{f(x)}" y="{f(y)}" width="{f(width)}" height="{f(height)}" '
            f'fill="{fill}" fill-opacity="{f(fill_opacity)}" stroke="{stroke}" stroke-opacity="{f(stroke_opacity)}" '
            f'data-name="{escape(district["name"])}" data-geometry="source-control-range"/>'
        )
        rendered += 1
    out.append(f'    <metadata data-source-control-district-envelopes="{rendered}"/>')
    out.append('  </g>')
    return "\n".join(out)


def residence_centroid(rows, prefix):
    points = [(float(r["x"]), float(r["z"])) for r in rows if r["id"].startswith(prefix)]
    if not points:
        raise ValueError(f"No residences for prefix {prefix}")
    return sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points), len(points)


def area_radius(area_ha):
    return math.sqrt(float(area_ha) * 10000.0 / math.pi)


def find_center_by_id(rows, rid):
    row = next((r for r in rows if r["id"] == rid), None)
    if row is None:
        raise KeyError(rid)
    return float(row["x"]), float(row["z"])


def square_center(core, name):
    sq = next(s for s in core["squares"] if s["name"] == name)
    return tuple(map(float, sq["centerXZ"]))


def park_center(core, name):
    park = next(p for p in core["parks"] if p["name"] == name)
    return tuple(map(float, park["centerXZ"]))


def lake_record(water):
    return next(w for w in water["waterBodies"] if w["id"] == "WATER-LAKE-01")


def sample_polyline(points, spacing):
    pts = [tuple(map(float, p)) for p in points]
    segments = []
    total = 0.0
    for a, b in zip(pts, pts[1:]):
        dx, dz = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dz)
        if length > 0:
            segments.append((a, b, dx, dz, length, total, total + length))
            total += length
    samples = []
    d = spacing / 2.0
    while d < total:
        for a, b, dx, dz, length, start, end in segments:
            if start <= d <= end:
                t = (d - start) / length
                x = a[0] + t * dx
                z = a[1] + t * dz
                tx, tz = dx / length, dz / length
                samples.append(((x, z), (tx, tz)))
                break
        d += spacing
    return samples


def green_structure_group(core, water, rows, cs, profile, visual_policy):
    if profile != "presentation":
        return '  <g id="16_GreenStructure" data-layer="green-structure" data-presentation="omitted-in-engineering"/>'

    landscape = visual_policy["landscapeSystem"]
    lake = lake_record(water)
    lake_center = tuple(map(float, lake["centerXZ"]))
    lawn = core["centralLawn"]
    lawn_center = ((lawn["xRange"][0] + lawn["xRange"][1]) / 2.0, (lawn["zRange"][0] + lawn["zRange"][1]) / 2.0)
    gate_south = next(e for e in core["entrances"] if e["id"] == "GATE-SOUTH")["position"]
    ceremonial = [
        (float(gate_south["x"]), float(gate_south["z"])),
        square_center(core, "迎宾广场"),
        square_center(core, "明德广场"),
        square_center(core, "求真广场"),
        find_center_by_id(rows, "CEN-02"),
        find_center_by_id(rows, "CEN-01"),
        lawn_center,
        lake_center,
    ]
    ecological = [
        park_center(core, "格物园"),
        lake_center,
        park_center(core, "文心园"),
        park_center(core, "艺境园"),
    ]

    out = ['  <g id="16_GreenStructure" data-layer="green-structure" data-geometry="presentation-reference">']
    out.append(f'    <polyline id="STEP6-AXIS-CEREMONIAL" class="step6-axis-ceremonial" points="{svg_points_attribute(cs.world_points_to_svg(ceremonial, profile))}" data-geometry="source-anchor-derived"/>')
    out.append(f'    <polyline id="STEP6-AXIS-ECOLOGICAL" class="step6-axis-eco" points="{svg_points_attribute(cs.world_points_to_svg(ecological, profile))}" data-geometry="source-anchor-derived"/>')

    # Riparian presentation buffers follow exact Step-4 water geometry; they do not define engineering setbacks.
    lake_stroke = float(landscape["riparianPresentation"]["lakeBufferStrokeMeters"])
    out.append(
        f'    <polygon id="STEP6-RIPARIAN-LAKE" class="step6-riparian-lake" points="{svg_points_attribute(cs.world_points_to_svg(lake["shorelineXZ"], profile))}" '
        f'stroke-width="{f(lake_stroke)}" data-geometry="visual-buffer-on-frozen-shoreline"/>'
    )
    stream_stroke = float(landscape["riparianPresentation"]["streamBufferStrokeMeters"])
    for suffix, chain in (("NORTH", water["mainStream"]["northInflowXZ"]), ("SOUTHEAST", water["mainStream"]["southeastOutflowXZ"])):
        out.append(
            f'    <polyline id="STEP6-RIPARIAN-STREAM-{suffix}" class="step6-riparian-stream" points="{svg_points_attribute(cs.world_points_to_svg(chain, profile))}" '
            f'stroke-width="{f(stream_stroke)}" data-geometry="visual-buffer-on-frozen-stream"/>'
        )

    area_min, area_max = map(float, landscape["lifeGreenHeartAreaHaRange"])
    r_min, r_max = area_radius(area_min), area_radius(area_max)
    greenheart_meta = []
    for key, cfg in landscape["formalLifeAreas"].items():
        cx, cz, count = residence_centroid(rows, cfg["residencePrefix"])
        sx, sy = cs.world_to_svg(cx, cz, profile)
        oid = key.upper()
        out.append(
            f'    <circle id="STEP6-GREENHEART-{oid}-OUTER" class="step6-greenheart-outer" cx="{f(sx)}" cy="{f(sy)}" r="{f(r_max)}" '
            f'data-area-ha-max="{f(area_max)}" data-center-rule="residence-centroid" data-residence-count="{count}"/>'
        )
        out.append(
            f'    <circle id="STEP6-GREENHEART-{oid}-INNER" class="step6-greenheart-inner" cx="{f(sx)}" cy="{f(sy)}" r="{f(r_min)}" '
            f'data-area-ha-min="{f(area_min)}" data-center-rule="residence-centroid" data-residence-count="{count}"/>'
        )
        greenheart_meta.append((key, cfg["name"], cx, cz, count))

    tree_count = 0
    seasonal_by_id = {p["id"]: p for p in core.get("seasonalPaths", [])}
    for path_id, avenue in landscape["seasonalAvenues"].items():
        source_path = seasonal_by_id[path_id]
        spacing = float(avenue["symbolSpacingMeters"])
        offset = float(avenue["sideOffsetMeters"])
        css = "step6-tree-cherry" if avenue["species"] == "cherry" else "step6-tree-ginkgo"
        samples = sample_polyline(source_path["centerlineXZ"], spacing)
        for i, (point, tangent) in enumerate(samples, 1):
            nx, nz = -tangent[1], tangent[0]
            for side_name, sign in (("L", 1.0), ("R", -1.0)):
                world = (point[0] + sign * nx * offset, point[1] + sign * nz * offset)
                sx, sy = cs.world_to_svg(world[0], world[1], profile)
                out.append(
                    f'    <circle id="STEP6-TREE-{path_id}-{i:02d}-{side_name}" class="{css}" cx="{f(sx)}" cy="{f(sy)}" r="5" '
                    f'data-species="{avenue["species"]}" data-geometry="presentation-symbol-derived-from-path"/>'
                )
                tree_count += 1

    out.append(f'    <metadata data-life-green-hearts="4" data-seasonal-tree-symbols="{tree_count}" data-greenheart-area-ha-range="{f(area_min)}-{f(area_max)}"/>')
    out.append('  </g>')
    return "\n".join(out)


def label_group(core, water, rows, cs, profile, visual_policy):
    if profile != "presentation":
        return '  <g id="17_PresentationLabels" data-layer="presentation-labels" data-presentation="omitted-in-engineering"/>'
    out = ['  <g id="17_PresentationLabels" data-layer="presentation-labels">']

    # District labels use source range centers; north life uses its residence centroid because source omits xRange.
    for district in core["districts"]:
        if "xRange" in district and "zRange" in district:
            x = (float(district["xRange"][0]) + float(district["xRange"][1])) / 2.0
            z = (float(district["zRange"][0]) + float(district["zRange"][1])) / 2.0
        elif district["id"] == "DIST-NORTH-LIFE":
            x, z, _ = residence_centroid(rows, "RES-N-")
        else:
            continue
        sx, sy = cs.world_to_svg(x, z, profile)
        out.append(f'    <text id="STEP6-LABEL-{district["id"]}" class="step6-district-label" x="{f(sx)}" y="{f(sy)}" text-anchor="middle">{escape(district["name"])}</text>')

    for key, life in visual_policy["landscapeSystem"]["formalLifeAreas"].items():
        x, z, _ = residence_centroid(rows, life["residencePrefix"])
        sx, sy = cs.world_to_svg(x, z, profile)
        out.append(f'    <text id="STEP6-LIFE-{key.upper()}" class="step6-life-label" x="{f(sx)}" y="{f(sy - 125)}" text-anchor="middle">{escape(life["name"])}</text>')

    row_map = {r["id"]: r for r in rows}
    for rid, label in MAJOR_LABEL_IDS.items():
        row = row_map[rid]
        if rid == "HSP-02":
            continue
        sx, sy = cs.world_to_svg(float(row["x"]), float(row["z"]), profile)
        out.append(f'    <text id="STEP6-MAJOR-{rid}" class="step6-major-label" x="{f(sx)}" y="{f(sy - 26)}" text-anchor="middle">{escape(label)}</text>')

    # Axis captions use existing source anchors and do not create new geometry.
    axis1 = cs.world_to_svg(-45, -445, profile)
    axis2 = cs.world_to_svg(640, 430, profile)
    out.append(f'    <text class="step6-axis-label" x="{f(axis1[0])}" y="{f(axis1[1])}" transform="rotate(-90 {f(axis1[0])} {f(axis1[1])})">南北礼仪轴</text>')
    out.append(f'    <text class="step6-axis-label" x="{f(axis2[0])}" y="{f(axis2[1])}">东西生态景观轴</text>')
    out.append('  </g>')
    return "\n".join(out)


def legend_group(profile, visual_policy):
    if profile != "presentation":
        return '  <g id="18_Step6Legend" data-layer="step6-legend" data-presentation="omitted-in-engineering"/>'
    brand = visual_policy["brand"]
    note = visual_policy["presentation"]["legendNote"]
    return "\n".join([
        '  <g id="18_Step6Legend" data-layer="step6-legend">',
        '    <text class="step6-legend-title" x="300" y="3070">STEP 6 · 景观与建筑语言</text>',
        f'    <rect x="300" y="3088" width="18" height="18" rx="3" fill="{brand["jiangchengBlue"]}"/>',
        '    <text class="step6-legend-note" x="326" y="3102">江城蓝：识别/地标强调</text>',
        f'    <rect x="540" y="3088" width="18" height="18" rx="3" fill="{brand["ginkgoGold"]}"/>',
        '    <text class="step6-legend-note" x="566" y="3102">银杏金：季节与重点辅助</text>',
        '    <text class="step6-legend-note" x="900" y="3102">建筑采用暖灰、砖、玻璃、深灰金属的低饱和统一体系</text>',
        f'    <text class="step6-legend-note" x="300" y="3130">{escape(note)}</text>',
        '  </g>',
    ])


def render(profile, core, city_roads, wall, internal, water, cfg, sports, step5_policy, visual_policy, rows, cs):
    svg = step5.render(profile, core, city_roads, wall, internal, water, cfg, rows, sports, step5_policy, cs)
    svg = svg.replace("江城大学总平面 R6 — Step 5", "江城大学总平面 R6 — Step 6")
    svg = svg.replace("generator=Tools/generate_svg_step5.py;", "generator=Tools/generate_svg_step6.py;")
    svg = svg.replace("step=5;", "step=6; presentationOverlays=reference-only;")
    svg = svg.replace("Step 5 · 建筑 / 56栋住宿 / 体育设施", "Step 6 · 景观 / 分区 / 建筑语言 / 展示层级")
    svg = inject_visual_styles(svg, profile, rows, visual_policy, step5_policy)

    # New Step-6 layers are reference/presentation overlays only. Existing Step-5 elements are untouched.
    district = district_group(core, cs, profile, visual_policy)
    green = green_structure_group(core, water, rows, cs, profile, visual_policy)
    labels = label_group(core, water, rows, cs, profile, visual_policy)
    legend = legend_group(profile, visual_policy)
    svg = svg.replace('  <g id="03_PerimeterWall"', district + '\n  <g id="03_PerimeterWall"', 1)
    svg = svg.replace('  <g id="05_InternalRoads"', green + '\n  <g id="05_InternalRoads"', 1)
    svg = svg.replace('  <g id="12_Labels"', labels + '\n  <g id="12_Labels"', 1)
    svg = svg.replace('</svg>', legend + '\n</svg>', 1)
    return svg


def main():
    core, city_roads, wall, internal, water, cfg, sports, step5_policy, visual_policy, rows = load_all()
    cs = SvgCoordinateSystem.from_file(step5.COORD)
    # Force assignment validation before any output is written.
    assignments = building_style_assignment(rows, visual_policy, step5_policy)
    if len(assignments) != 142:
        raise SystemExit(f"Step 6 building-style assignment count mismatch: {len(assignments)} != 142")
    OUT.mkdir(parents=True, exist_ok=True)
    for profile, path in OUTPUTS.items():
        path.write_text(
            render(profile, core, city_roads, wall, internal, water, cfg, sports, step5_policy, visual_policy, rows, cs),
            encoding="utf-8",
        )
        print(f"WROTE {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

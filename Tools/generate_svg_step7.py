#!/usr/bin/env python3
"""Generate Step-7 Jiangcheng University delivery SVGs.

Step 7 is a delivery-structure pass over Step 6. It may:
- rename top-level SVG groups into stable Figma layer names;
- physically prune dense technical labels from the presentation SVG;
- rebuild a curated primary/secondary/district/road/water label hierarchy;
- rebuild the compact legend and north/scale metadata.

It may NOT change any Step-6 engineering geometry.
"""
from __future__ import annotations

import math
import re
from html import escape
from pathlib import Path

import generate_svg_step6 as step6
import generate_svg_step4 as step4
from svg_coordinates import SvgCoordinateSystem, format_svg_number

ROOT = Path(__file__).resolve().parents[1]
DELIVERY_POLICY = ROOT / "CampusData/svg/step7_delivery_policy_r6.json"
OUT = ROOT / "Artifacts/SVG"
PATCH = "PATCH-2026-09-13-R6"

OUTPUTS = {
    "engineering": OUT / "Jiangcheng-University-MasterPlan-Step7-R6-Engineering.svg",
    "presentation": OUT / "Jiangcheng-University-MasterPlan-Step7-R6-Figma.svg",
}


def f(value):
    return format_svg_number(value)


def load_all():
    core, city_roads, wall, internal, water, cfg, sports, step5_policy, visual_policy, rows = step6.load_all()
    delivery = step6.step5.load_json(DELIVERY_POLICY)
    if delivery.get("sourcePatchVersion") != PATCH:
        raise SystemExit("Step 7 delivery policy patch mismatch")
    return core, city_roads, wall, internal, water, cfg, sports, step5_policy, visual_policy, delivery, rows


def rename_layers(svg, layer_map):
    for old, new in layer_map.items():
        svg = svg.replace(f'id="{old}"', f'id="{new}"', 1)
    return svg


def remove_group(svg, group_id):
    # Target groups contain no nested <g> elements in Step 6, so bounded non-greedy removal is deterministic.
    paired = re.compile(rf'\n?\s*<g id="{re.escape(group_id)}"\b[^>]*>.*?</g>\s*', re.S)
    svg2, count = paired.subn("\n", svg, count=1)
    if count:
        return svg2
    self_closing = re.compile(rf'\n?\s*<g id="{re.escape(group_id)}"\b[^>]*/>\s*')
    svg2, count = self_closing.subn("\n", svg, count=1)
    if not count:
        raise ValueError(f"Step 7 prune group not found: {group_id}")
    return svg2


def inject_styles(svg):
    extra = '''
      .step7-primary { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:22px; font-weight:750; fill:#27343d; paint-order:stroke; stroke:#fbfaf6; stroke-width:6; stroke-linejoin:round; pointer-events:none; }
      .step7-secondary { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:15px; font-weight:650; fill:#3f494f; paint-order:stroke; stroke:#fbfaf6; stroke-width:4; stroke-linejoin:round; pointer-events:none; }
      .step7-service { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:12px; font-weight:600; fill:#665f51; paint-order:stroke; stroke:#fbfaf6; stroke-width:3.5; stroke-linejoin:round; pointer-events:none; }
      .step7-life { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:28px; font-weight:800; fill:#173A5E; paint-order:stroke; stroke:#fbfaf6; stroke-width:6; pointer-events:none; }
      .step7-district { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:17px; font-weight:650; fill:#677077; fill-opacity:.82; paint-order:stroke; stroke:#fbfaf6; stroke-width:4; pointer-events:none; }
      .step7-road { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:17px; font-weight:650; fill:#566169; paint-order:stroke; stroke:#fbfaf6; stroke-width:4; pointer-events:none; }
      .step7-city-road { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:25px; font-weight:700; fill:#343b40; paint-order:stroke; stroke:#fbfaf6; stroke-width:5; letter-spacing:1.5px; pointer-events:none; }
      .step7-water-primary { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:25px; font-weight:800; fill:#356a81; paint-order:stroke; stroke:#eaf6fa; stroke-width:5; pointer-events:none; }
      .step7-water-secondary { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:13px; font-weight:650; fill:#52788a; paint-order:stroke; stroke:#f2f8fa; stroke-width:3; pointer-events:none; }
      .step7-open { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:13px; font-weight:650; fill:#5c7054; paint-order:stroke; stroke:#fbfaf6; stroke-width:3.5; pointer-events:none; }
      .step7-axis { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:14px; font-weight:700; fill:#647467; paint-order:stroke; stroke:#fbfaf6; stroke-width:3.5; pointer-events:none; }
      .step7-legend-title { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:16px; font-weight:750; fill:#173A5E; }
      .step7-legend-text { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:12px; fill:#4f575c; }
      .step7-legend-small { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; font-size:11px; fill:#666d71; }
'''
    return svg.replace("    </style>", extra + "    </style>", 1)


def row_map(rows):
    return {r["id"]: r for r in rows}


def building_label(entry, rows_by_id, cs, profile, css, oid_prefix):
    row = rows_by_id[entry["buildingID"]]
    sx, sy = cs.world_to_svg(float(row["x"]), float(row["z"]), profile)
    dx = float(entry.get("dx", 0))
    dy = float(entry.get("dy", -22))
    return (
        f'    <text id="{oid_prefix}-{entry["buildingID"]}" class="{css}" '
        f'x="{f(sx + dx)}" y="{f(sy + dy)}" text-anchor="middle">{escape(entry["label"])}</text>'
    )


def place_label_groups(core, rows, cs, profile, policy):
    if profile != "presentation":
        return (
            '  <g id="14_LABEL_Primary_Places" data-presentation="omitted-in-engineering"/>\n'
            '  <g id="15_LABEL_Secondary_POI" data-presentation="omitted-in-engineering"/>'
        )
    rows_by_id = row_map(rows)
    primary = ['  <g id="14_LABEL_Primary_Places" data-layer="primary-place-labels">']
    for entry in policy["primaryPlaces"]:
        primary.append(building_label(entry, rows_by_id, cs, profile, "step7-primary", "STEP7-PRIMARY"))
    primary.append('  </g>')

    secondary = ['  <g id="15_LABEL_Secondary_POI" data-layer="secondary-poi-open-space-labels">']
    for entry in policy["secondaryPlaces"]:
        secondary.append(building_label(entry, rows_by_id, cs, profile, "step7-secondary", "STEP7-SECONDARY"))
    for index, entry in enumerate(policy["lifeServicePOIs"], 1):
        row = rows_by_id[entry["buildingID"]]
        sx, sy = cs.world_to_svg(float(row["x"]), float(row["z"]), profile)
        secondary.append(
            f'    <text id="STEP7-SERVICE-{index:02d}" class="step7-service" x="{f(sx)}" y="{f(sy + 24)}" text-anchor="middle">{escape(entry["label"])}</text>'
        )
    for index, sq in enumerate(core["squares"], 1):
        sx, sy = cs.world_to_svg(float(sq["centerXZ"][0]), float(sq["centerXZ"][1]), profile)
        secondary.append(f'    <text id="STEP7-SQUARE-{index:02d}" class="step7-open" x="{f(sx + 14)}" y="{f(sy - 12)}">{escape(sq["name"])}</text>')
    for index, park in enumerate(core["parks"], 1):
        if "centerXZ" in park:
            x, z = map(float, park["centerXZ"])
        else:
            x = (float(park["range"]["x"][0]) + float(park["range"]["x"][1])) / 2.0
            z = (float(park["range"]["z"][0]) + float(park["range"]["z"][1])) / 2.0
        sx, sy = cs.world_to_svg(x, z, profile)
        secondary.append(f'    <text id="STEP7-PARK-{index:02d}" class="step7-open" x="{f(sx)}" y="{f(sy)}" text-anchor="middle">{escape(park["name"])}</text>')
    lawn = core["centralLawn"]
    lx = (float(lawn["xRange"][0]) + float(lawn["xRange"][1])) / 2.0
    lz = (float(lawn["zRange"][0]) + float(lawn["zRange"][1])) / 2.0
    sx, sy = cs.world_to_svg(lx, lz, profile)
    secondary.append(f'    <text id="STEP7-LAWN" class="step7-open" x="{f(sx)}" y="{f(sy)}" text-anchor="middle">{escape(lawn["name"])}</text>')
    for path in core.get("seasonalPaths", []):
        midpoint, rotation = step4.polyline_midpoint(path["centerlineXZ"])
        sx, sy = cs.world_to_svg(midpoint[0], midpoint[1], profile)
        label = f'{path["name"]} / {path["alias"]}'
        secondary.append(
            f'    <text id="STEP7-SEASONAL-{path["id"]}" class="step7-open" x="{f(sx)}" y="{f(sy - 10)}" text-anchor="middle" '
            f'transform="rotate({f(rotation)} {f(sx)} {f(sy - 10)})">{escape(label)}</text>'
        )
    secondary.append('  </g>')
    return "\n".join(primary + secondary)


def district_life_group(core, rows, cs, profile, policy):
    if profile != "presentation":
        return '  <g id="16_LABEL_Districts_Life" data-presentation="omitted-in-engineering"/>'
    out = ['  <g id="16_LABEL_Districts_Life" data-layer="district-life-axis-labels">']
    for district in core["districts"]:
        if "xRange" in district and "zRange" in district:
            x = (float(district["xRange"][0]) + float(district["xRange"][1])) / 2.0
            z = (float(district["zRange"][0]) + float(district["zRange"][1])) / 2.0
        elif district["id"] == "DIST-NORTH-LIFE":
            x, z, _ = step6.residence_centroid(rows, "RES-N-")
        else:
            continue
        sx, sy = cs.world_to_svg(x, z, profile)
        out.append(f'    <text id="STEP7-DIST-{district["id"]}" class="step7-district" x="{f(sx)}" y="{f(sy)}" text-anchor="middle">{escape(district["name"])}</text>')
    for key, life in step6.step5.load_json(step6.VISUAL_POLICY)["landscapeSystem"]["formalLifeAreas"].items():
        x, z, _ = step6.residence_centroid(rows, life["residencePrefix"])
        sx, sy = cs.world_to_svg(x, z, profile)
        out.append(f'    <text id="STEP7-LIFE-{key.upper()}" class="step7-life" x="{f(sx)}" y="{f(sy - 125)}" text-anchor="middle">{escape(life["name"])}</text>')
    axis1 = cs.world_to_svg(-45, -445, profile)
    axis2 = cs.world_to_svg(640, 430, profile)
    out.append(f'    <text id="STEP7-AXIS-NS" class="step7-axis" x="{f(axis1[0])}" y="{f(axis1[1])}" transform="rotate(-90 {f(axis1[0])} {f(axis1[1])})">南北礼仪轴</text>')
    out.append(f'    <text id="STEP7-AXIS-EW" class="step7-axis" x="{f(axis2[0])}" y="{f(axis2[1])}">东西生态景观轴</text>')
    out.append('  </g>')
    return "\n".join(out)


def derived_chenghu_path(water):
    lake = next(w for w in water["waterBodies"] if w["id"] == "WATER-LAKE-01")
    pts = step4.offset_closed_polygon(lake["shorelineXZ"], 25.0)
    return pts + [pts[0]]


def roads_water_group(city_roads, internal, water, cs, profile, policy):
    if profile != "presentation":
        return '  <g id="17_LABEL_Roads_Water" data-presentation="omitted-in-engineering"/>'
    out = ['  <g id="17_LABEL_Roads_Water" data-layer="road-water-labels">']
    city_by_id = {r["id"]: r for r in city_roads["roads"]}
    for rid in policy["roadLabels"]["externalRoadIDs"]:
        road = city_by_id[rid]
        label_world, rotation = step4.ROAD_LABELS[rid]
        sx, sy = cs.world_to_svg(label_world[0], label_world[1], profile)
        out.append(
            f'    <text id="STEP7-ROAD-{rid}" class="step7-city-road" x="{f(sx)}" y="{f(sy)}" text-anchor="middle" '
            f'transform="rotate({f(rotation)} {f(sx)} {f(sy)})">{escape(road["name"])}</text>'
        )
    internal_by_id = {r["id"]: r for r in internal["internalRoads"]}
    for rid in policy["roadLabels"]["internalRoadIDs"]:
        road = internal_by_id[rid]
        centerline = derived_chenghu_path(water) if rid == "PATH-CHENGHU" else road["centerlineXZ"]
        midpoint, rotation = step4.polyline_midpoint(centerline)
        sx, sy = cs.world_to_svg(midpoint[0], midpoint[1], profile)
        label = policy["roadLabels"]["displayOverrides"].get(rid, road["name"])
        out.append(
            f'    <text id="STEP7-ROAD-{rid}" class="step7-road" x="{f(sx)}" y="{f(sy - 9)}" text-anchor="middle" '
            f'transform="rotate({f(rotation)} {f(sx)} {f(sy - 9)})">{escape(label)}</text>'
        )
    for body in water["waterBodies"]:
        sx, sy = cs.world_to_svg(float(body["centerXZ"][0]), float(body["centerXZ"][1]), profile)
        css = "step7-water-primary" if body["id"] == policy["waterLabels"]["primaryWaterID"] else "step7-water-secondary"
        dy = -18 if css == "step7-water-primary" else -10
        out.append(f'    <text id="STEP7-WATER-{body["id"]}" class="{css}" x="{f(sx)}" y="{f(sy + dy)}" text-anchor="middle">{escape(body["name"])}</text>')
    out.append('  </g>')
    return "\n".join(out)


def legend_group(profile, policy):
    if profile != "presentation":
        return '  <g id="18_META_Legend" data-presentation="omitted-in-engineering"/>'
    notes = policy["legend"]["notes"]
    out = [
        '  <g id="18_META_Legend" data-layer="delivery-legend">',
        f'    <text class="step7-legend-title" x="300" y="3000">{escape(policy["legend"]["title"])}</text>',
        '    <rect x="300" y="3020" width="18" height="12" fill="#ded8c9" stroke="#596067" stroke-width="2"/>',
        '    <text class="step7-legend-text" x="328" y="3031">建筑/设施控制轮廓</text>',
        '    <line x1="520" y1="3026" x2="575" y2="3026" stroke="#757b80" stroke-width="8" stroke-linecap="round"/>',
        '    <text class="step7-legend-text" x="586" y="3031">校园道路</text>',
        '    <rect x="720" y="3019" width="24" height="14" rx="5" fill="#b7d9e8" stroke="#6f9fb5" stroke-width="2"/>',
        '    <text class="step7-legend-text" x="754" y="3031">水体</text>',
        '    <circle cx="860" cy="3026" r="8" fill="#cbdcbd" fill-opacity=".35" stroke="#78906f" stroke-width="2" stroke-dasharray="5 4"/>',
        '    <text class="step7-legend-text" x="878" y="3031">参考/控制范围</text>',
    ]
    y = 3054
    for note in notes:
        out.append(f'    <text class="step7-legend-small" x="300" y="{y}">• {escape(note)}</text>')
        y += 19
    out.append('  </g>')
    return "\n".join(out)


def north_scale_group(profile):
    if profile == "presentation":
        return "\n".join([
            '  <g id="19_META_North_Scale" data-layer="north-scale">',
            '    <text class="legend" x="4020" y="190" text-anchor="middle">N</text>',
            '    <path d="M 4020 205 L 4020 285 M 4007 223 L 4020 205 L 4033 223" fill="none" stroke="#173A5E" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>',
            '    <line x1="3370" y1="3085" x2="3870" y2="3085" stroke="#30353a" stroke-width="6"/>',
            '    <line x1="3370" y1="3073" x2="3370" y2="3097" stroke="#30353a" stroke-width="4"/>',
            '    <line x1="3870" y1="3073" x2="3870" y2="3097" stroke="#30353a" stroke-width="4"/>',
            '    <text class="step7-legend-small" x="3370" y="3064">0</text>',
            '    <text class="step7-legend-small" x="3870" y="3064" text-anchor="end">500 m</text>',
            '  </g>',
        ])
    return '  <g id="19_META_North_Scale" data-layer="north-scale-engineering"/>'


def replace_group(svg, group_id, replacement):
    paired = re.compile(rf'\s*<g id="{re.escape(group_id)}"\b[^>]*>.*?</g>', re.S)
    svg2, count = paired.subn("\n" + replacement, svg, count=1)
    if count:
        return svg2
    self_closing = re.compile(rf'\s*<g id="{re.escape(group_id)}"\b[^>]*/>')
    svg2, count = self_closing.subn("\n" + replacement, svg, count=1)
    if not count:
        raise ValueError(f"Step 7 replace group not found: {group_id}")
    return svg2


def render(profile, core, city_roads, wall, internal, water, cfg, sports, step5_policy, visual_policy, delivery, rows, cs):
    svg = step6.render(profile, core, city_roads, wall, internal, water, cfg, sports, step5_policy, visual_policy, rows, cs)
    svg = svg.replace("江城大学总平面 R6 — Step 6", "江城大学总平面 R6 — Step 7")
    svg = svg.replace("generator=Tools/generate_svg_step6.py;", "generator=Tools/generate_svg_step7.py;")
    svg = svg.replace("step=6;", "step=7; deliveryLayerSchema=step7;")
    svg = svg.replace("Step 6 · 景观 / 分区 / 建筑语言 / 展示层级", "Step 7 · Figma交付层级 / 最终标签 / 图例")
    svg = inject_styles(svg)
    svg = rename_layers(svg, delivery["figmaLayerMap"])

    if profile == "presentation":
        for group_id in delivery["presentationPruneGroups"]:
            svg = remove_group(svg, group_id)
    # Replace old north/scale group in both profiles so the final layer name and content are stable.
    svg = replace_group(svg, "19_META_North_Scale", north_scale_group(profile))

    final_groups = "\n".join([
        place_label_groups(core, rows, cs, profile, delivery),
        district_life_group(core, rows, cs, profile, delivery),
        roads_water_group(city_roads, internal, water, cs, profile, delivery),
        legend_group(profile, delivery),
    ])
    svg = svg.replace("</svg>", final_groups + "\n</svg>", 1)
    return svg


def main():
    core, city_roads, wall, internal, water, cfg, sports, step5_policy, visual_policy, delivery, rows = load_all()
    cs = SvgCoordinateSystem.from_file(step6.step5.COORD)
    OUT.mkdir(parents=True, exist_ok=True)
    for profile, path in OUTPUTS.items():
        path.write_text(
            render(profile, core, city_roads, wall, internal, water, cfg, sports, step5_policy, visual_policy, delivery, rows, cs),
            encoding="utf-8",
        )
        print(f"WROTE {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate Step-5 Jiangcheng University masterplan SVG.

Step 5 starts from the deterministic Step-4 render string and only fills the
previously empty 08_Buildings / 09_Residential / 10_Sports / 11_POI layers.
This guarantees Step-4 perimeter, road, water and landscape geometry is not moved.
"""
from __future__ import annotations

import csv
import json
from html import escape
from pathlib import Path

from svg_coordinates import SvgCoordinateSystem, format_svg_number
from generate_svg_step4 import (
    load_json,
    render as render_step4,
    CORE,
    CITY_ROADS,
    WALL,
    INTERNAL,
    WATER,
    COORD,
)

ROOT = Path(__file__).resolve().parents[1]
BUILDINGS = ROOT / "CampusData/svg/building_placement_r6.csv"
SPORTS = ROOT / "CampusData/svg/outdoor_sports_r6.json"
POLICY = ROOT / "CampusData/svg/step5_render_policy_r6.json"
OUT = ROOT / "Artifacts/SVG"
PATCH = "PATCH-2026-09-13-R6"

OUTPUTS = {
    "engineering": OUT / "Jiangcheng-University-MasterPlan-Step5-R6-Engineering.svg",
    "presentation": OUT / "Jiangcheng-University-MasterPlan-Step5-R6-Figma.svg",
}


def load_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def number(value, field, row_id):
    if value is None or str(value).strip() == "":
        raise ValueError(f"{row_id}: missing {field}")
    return float(value)


def maybe_number(value):
    if value is None or str(value).strip() == "":
        return None
    return float(value)


def building_class(row):
    bid = row["id"]
    if bid.startswith("HSP-"):
        return "building-footprint hospital-building"
    if bid.startswith("CEN-"):
        return "building-footprint central-building"
    if bid.startswith("RDI-"):
        return "building-footprint research-building"
    if bid.startswith("LIFE-"):
        return "building-footprint life-building"
    if bid.startswith("OPS-"):
        return "building-footprint ops-building"
    if bid.startswith("ATH-") or bid.startswith("PE-"):
        return "building-footprint sports-building"
    return "building-footprint academic-building"


def sport_class(kind):
    return {
        "basketball": "sport-control sport-basketball",
        "table_tennis": "sport-control sport-table-tennis",
        "tennis": "sport-control sport-tennis",
        "volleyball": "sport-control sport-volleyball",
        "badminton": "sport-control sport-badminton",
        "five_a_side": "sport-control sport-football",
    }.get(kind, "sport-control sport-generic")


def rect_element(oid, css, sx, sy, length, width, rotation, extra=""):
    f = format_svg_number
    x = sx - length / 2.0
    y = sy - width / 2.0
    return (
        f'<rect id="{escape(oid)}" class="{css}" x="{f(x)}" y="{f(y)}" '
        f'width="{f(length)}" height="{f(width)}" '
        f'transform="rotate({f(rotation)} {f(sx)} {f(sy)})" {extra}/>'
    )


def label_element(text, sx, sy, css="building-id"):
    f = format_svg_number
    return f'<text class="{css}" x="{f(sx)}" y="{f(sy - 7)}" text-anchor="middle">{escape(text)}</text>'


def render_buildings(profile, rows, policy, cs):
    f = format_svg_number
    sports_surface = set(policy["buildingTableSpecialRouting"]["sportsSurfaceIDs"])
    sports_stands = set(policy["buildingTableSpecialRouting"]["sportsStandIDs"])
    routed = sports_surface | sports_stands
    overlay_by_id = {x["id"]: x for x in policy["hospitalOverlays"]}
    out = ['  <g id="08_Buildings" data-layer="buildings">']
    labels = []
    rendered = 0

    for row in rows:
        bid = row["id"]
        if bid.startswith("RES-") or bid in routed:
            continue
        if bid in overlay_by_id:
            ov = overlay_by_id[bid]
            sx, sy = cs.world_to_svg(ov["planCenterXZ"][0], ov["planCenterXZ"][1], profile)
            out.append("    " + rect_element(
                bid,
                "building-footprint hospital-tower-overlay",
                sx,
                sy,
                float(ov["lengthMeters"]),
                float(ov["widthMeters"]),
                float(ov["rotationY"]),
                f'data-parent-id="{ov["parentBuildingID"]}" data-ground-independent="false" data-render-mode="upper_tower_overlay" data-plan-center-source="R6-R5"',
            ))
            labels.append("    " + label_element(bid, sx, sy, "building-id hospital-id"))
            rendered += 1
            continue

        x = number(row["x"], "x", bid)
        z = number(row["z"], "z", bid)
        length = number(row["length"], "length", bid)
        width = number(row["width"], "width", bid)
        rotation = number(row["rotationY"], "rotationY", bid)
        sx, sy = cs.world_to_svg(x, z, profile)
        name = row["name"] or bid
        floors = row["floors"] or ""
        extra = (
            f'data-name="{escape(name)}" data-world-x="{f(x)}" data-world-z="{f(z)}" '
            f'data-length-m="{f(length)}" data-width-m="{f(width)}" data-rotation-y="{f(rotation)}" '
            f'data-floors="{escape(floors)}" data-source="{escape(row["source"])}"'
        )
        out.append("    " + rect_element(bid, building_class(row), sx, sy, length, width, rotation, extra))
        labels.append("    " + label_element(bid, sx, sy))
        rendered += 1

    out.append(f'    <metadata data-rendered-building-records="{rendered}"/>')
    out.append('  </g>')
    return "\n".join(out), labels


def render_residences(profile, rows, policy, cs):
    f = format_svg_number
    residence_policy = policy["residenceFootprints"]
    out = ['  <g id="09_Residential" data-layer="residential">']
    labels = []
    count = 0

    for row in rows:
        bid = row["id"]
        if not bid.startswith("RES-"):
            continue
        kind = row["residenceType"]
        p = residence_policy[kind]
        x = number(row["x"], "x", bid)
        z = number(row["z"], "z", bid)
        rotation = number(row["rotationY"], "rotationY", bid)
        sx, sy = cs.world_to_svg(x, z, profile)

        if kind == "undergraduate":
            length_min = float(p["lengthMinMeters"])
            length_max = float(p["lengthMaxMeters"])
            width = float(p["widthMeters"])
            # Max envelope first, then the source minimum body. No hidden midpoint.
            out.append("    " + rect_element(
                f"{bid}-MAX",
                "residence-max-envelope",
                sx,
                sy,
                length_max,
                width,
                rotation,
                f'data-parent-id="{bid}" data-length-max-m="{f(length_max)}" data-width-m="{f(width)}"',
            ))
            out.append("    " + rect_element(
                bid,
                "residence-footprint residence-undergraduate",
                sx,
                sy,
                length_min,
                width,
                rotation,
                f'data-residence-type="undergraduate" data-length-min-m="{f(length_min)}" data-length-max-m="{f(length_max)}" data-width-m="{f(width)}" data-floors-range="{p["floorsMin"]}-{p["floorsMax"]}" data-render-mode="range-not-midpoint"',
            ))
        else:
            length = float(p["lengthMeters"])
            width = float(p["widthMeters"])
            out.append("    " + rect_element(
                bid,
                f"residence-footprint residence-{kind}",
                sx,
                sy,
                length,
                width,
                rotation,
                f'data-residence-type="{kind}" data-length-m="{f(length)}" data-width-m="{f(width)}" data-floors="{p["floors"]}" data-render-mode="exact-control-footprint"',
            ))
        labels.append("    " + label_element(bid, sx, sy, "residence-id"))
        count += 1

    out.append(f'    <metadata data-residence-records="{count}" data-template-count="{residence_policy["templateCount"]}"/>')
    out.append('  </g>')
    return "\n".join(out), labels


def render_track_or_surface(row, profile, cs, policy):
    f = format_svg_number
    bid = row["id"]
    x = number(row["x"], "x", bid)
    z = number(row["z"], "z", bid)
    length = number(row["length"], "length", bid)
    width = number(row["width"], "width", bid)
    rotation = number(row["rotationY"], "rotationY", bid)
    sx, sy = cs.world_to_svg(x, z, profile)
    if bid in {"ATH-05", "ATH-11"}:
        outer = rect_element(
            bid,
            "sports-track",
            sx,
            sy,
            length,
            width,
            rotation,
            f'data-geometry="schematic-within-control-footprint" data-length-m="{f(length)}" data-width-m="{f(width)}"',
        )
        inner_l = max(0.0, length - 44.0)
        inner_w = max(0.0, width - 44.0)
        inner = rect_element(
            f"{bid}-INFIELD",
            "sports-infield",
            sx,
            sy,
            inner_l,
            inner_w,
            rotation,
            'data-derived="visual-infield-only"',
        )
        return [outer, inner], (sx, sy)
    css = "sports-plaza" if bid == "ATH-02" else "sports-stand"
    return [rect_element(
        bid,
        css,
        sx,
        sy,
        length,
        width,
        rotation,
        f'data-length-m="{f(length)}" data-width-m="{f(width)}" data-source="{escape(row["source"])}"',
    )], (sx, sy)


def render_sports(profile, rows, sports, policy, cs):
    f = format_svg_number
    sports_surface = set(policy["buildingTableSpecialRouting"]["sportsSurfaceIDs"])
    sports_stands = set(policy["buildingTableSpecialRouting"]["sportsStandIDs"])
    out = ['  <g id="10_Sports" data-layer="sports">']
    labels = []

    # Major sports surfaces / stands that already live in the building placement table.
    routed_count = 0
    for row in rows:
        if row["id"] not in sports_surface | sports_stands:
            continue
        elems, center = render_track_or_surface(row, profile, cs, policy)
        out.extend("    " + e for e in elems)
        labels.append("    " + label_element(row["id"], center[0], center[1], "sport-id"))
        routed_count += 1

    footprint_count = 0
    marker_count = 0
    for item in sports["outdoorSports"]:
        oid = item["id"]
        p = item["position"]
        sx, sy = cs.world_to_svg(float(p["x"]), float(p["z"]), profile)
        rotation = float(item.get("rotationY", 0.0))
        footprint = item.get("controlFootprint")
        if footprint:
            length = float(footprint["length"])
            width = float(footprint["width"])
            out.append("    " + rect_element(
                oid,
                sport_class(item["type"]),
                sx,
                sy,
                length,
                width,
                rotation,
                f'data-sport-type="{item["type"]}" data-count="{item["count"]}" data-length-m="{f(length)}" data-width-m="{f(width)}" data-rotation-y="{f(rotation)}" data-source="{escape(item["source"])}"',
            ))
            footprint_count += 1
        else:
            out.append(
                f'    <circle id="{oid}" class="sport-marker-only" cx="{f(sx)}" cy="{f(sy)}" r="7" '
                f'data-sport-type="{item["type"]}" data-count="{item["count"]}" data-geometry="center-marker-only" data-source="{escape(item["source"])}"/>'
            )
            marker_count += 1
        labels.append("    " + label_element(f'{oid} ×{item["count"]}', sx, sy, "sport-id"))

    totals = sports["outdoorSportsTotals"]
    out.append(
        '    <metadata '
        f'data-routed-major-sports="{routed_count}" data-outdoor-sports-records="{len(sports["outdoorSports"])}" '
        f'data-control-footprints="{footprint_count}" data-marker-only="{marker_count}" '
        f'data-basketball-full-court-equivalent="{totals["basketballFullCourtEquivalent"]}" '
        f'data-table-tennis-tables="{totals["outdoorTableTennisTables"]}" '
        f'data-tennis-courts="{totals["tennisCourts"]}" data-volleyball-courts="{totals["volleyballCourts"]}" '
        f'data-badminton-courts="{totals["outdoorBadmintonCourts"]}" data-five-a-side-fields="{totals["fiveASideFootballFields"]}"/>'
    )
    out.append('  </g>')
    return "\n".join(out), labels


def render_poi(policy, cs, profile):
    f = format_svg_number
    # HSP-RSV-01 has a frozen center but no frozen parcel boundary, so Step 5 keeps it point-only.
    sx, sy = cs.world_to_svg(-1280, -830, profile)
    return "\n".join([
        '  <g id="11_POI" data-layer="step5-poi">',
        f'    <circle id="HSP-RSV-01" class="reserve-marker" cx="{f(sx)}" cy="{f(sy)}" r="9" data-geometry="center-marker-only"/>',
        f'    <text class="poi-id" x="{f(sx + 14)}" y="{f(sy - 10)}">HSP-RSV-01 医院二期预留</text>',
        '  </g>',
    ])


def inject_styles(svg):
    extra = '''
      .building-footprint { stroke:#596067; stroke-width:2; }
      .academic-building { fill:#ded8c9; }
      .central-building { fill:#d9c8a8; stroke:#6f6250; stroke-width:2.5; }
      .research-building { fill:#d0d7d9; }
      .hospital-building { fill:#e2c8c4; stroke:#8a5751; stroke-width:2.5; }
      .hospital-tower-overlay { fill:#c9948c; fill-opacity:.45; stroke:#793f38; stroke-width:3; stroke-dasharray:10 6; }
      .life-building { fill:#e5d4bd; }
      .ops-building { fill:#d1d1ca; }
      .sports-building { fill:#d7ddd0; }
      .residence-footprint { stroke:#7c715f; stroke-width:1.8; }
      .residence-undergraduate { fill:#eadfcb; }
      .residence-graduate { fill:#e2d5bf; }
      .residence-international { fill:#d9cbb2; }
      .residence-max-envelope { fill:none; stroke:#a89b87; stroke-width:1.3; stroke-dasharray:5 4; }
      .sports-track { fill:#cda79a; stroke:#8d675d; stroke-width:3; rx:70; ry:70; }
      .sports-infield { fill:#b8cda8; stroke:#f3eee5; stroke-width:2; rx:45; ry:45; }
      .sports-plaza { fill:#ded8cf; stroke:#999188; stroke-width:2; }
      .sports-stand { fill:#bbb8b0; stroke:#74716c; stroke-width:2; }
      .sport-control { stroke-width:2; fill-opacity:.62; }
      .sport-basketball { fill:#c8aa91; stroke:#96745b; }
      .sport-table-tennis { fill:#bdcfb7; stroke:#78906f; }
      .sport-tennis { fill:#b7c9a9; stroke:#718865; }
      .sport-volleyball { fill:#d8c7a0; stroke:#9a865c; }
      .sport-badminton { fill:#d4d5bc; stroke:#8d8e6c; }
      .sport-football { fill:#aec8a0; stroke:#66815a; }
      .sport-marker-only { fill:#C4A052; stroke:#715f38; stroke-width:2; }
      .reserve-marker { fill:none; stroke:#9a755c; stroke-width:2; stroke-dasharray:5 4; }
      .building-id, .residence-id, .sport-id, .poi-id { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",sans-serif; fill:#4c5257; pointer-events:none; }
      .building-id { font-size:10px; }
      .hospital-id { fill:#6f3934; font-weight:700; }
      .residence-id { font-size:8px; fill:#6f6557; }
      .sport-id { font-size:9px; fill:#5f604c; }
      .poi-id { font-size:12px; fill:#70543f; }
'''
    return svg.replace("    </style>", extra + "    </style>", 1)


def render(profile, core, city_roads, wall, internal, water, cfg, rows, sports, policy, cs):
    svg = render_step4(profile, core, city_roads, wall, internal, water, cfg, cs)
    svg = svg.replace("江城大学总平面 R6 — Step 4", "江城大学总平面 R6 — Step 5")
    svg = svg.replace("generator=Tools/generate_svg_step4.py;", "generator=Tools/generate_svg_step5.py;")
    svg = svg.replace("step=4;", "step=5;")
    svg = svg.replace("Step 4 · 内部道路 / 水系 / 广场 / 开放空间", "Step 5 · 建筑 / 56栋住宿 / 体育设施")
    svg = inject_styles(svg)

    building_group, building_labels = render_buildings(profile, rows, policy, cs)
    residence_group, residence_labels = render_residences(profile, rows, policy, cs)
    sports_group, sports_labels = render_sports(profile, rows, sports, policy, cs)
    poi_group = render_poi(policy, cs, profile)

    svg = svg.replace('  <g id="08_Buildings" data-step="future"/>', building_group, 1)
    svg = svg.replace('  <g id="09_Residential" data-step="future"/>', residence_group, 1)
    svg = svg.replace('  <g id="10_Sports" data-step="future"/>', sports_group, 1)
    svg = svg.replace('  <g id="11_POI" data-step="future"/>', poi_group, 1)

    label_payload = "\n".join(building_labels + residence_labels + sports_labels)
    svg = svg.replace(
        '  <g id="12_Labels" data-layer="step4-labels">',
        '  <g id="12_Labels" data-layer="step5-labels">\n' + label_payload,
        1,
    )
    return svg


def main():
    core = load_json(CORE)
    city_roads = load_json(CITY_ROADS)
    wall = load_json(WALL)
    internal = load_json(INTERNAL)
    water = load_json(WATER)
    cfg = load_json(COORD)
    sports = load_json(SPORTS)
    policy = load_json(POLICY)
    rows = load_csv(BUILDINGS)
    for source in (core, city_roads, wall, internal, water, cfg, sports, policy):
        if source.get("sourcePatchVersion") != PATCH:
            raise SystemExit(f"source patch mismatch: {source.get('sourcePatchVersion')}")
    if len(rows) != 204:
        raise SystemExit(f"building/facility record count mismatch: {len(rows)} != 204")
    residences = [r for r in rows if r["id"].startswith("RES-")]
    if len(residences) != 56:
        raise SystemExit(f"residence record count mismatch: {len(residences)} != 56")
    residence_counts = {}
    for r in residences:
        residence_counts[r["residenceType"]] = residence_counts.get(r["residenceType"], 0) + 1
    if residence_counts != {"graduate": 10, "international": 4, "undergraduate": 42}:
        raise SystemExit(f"residence type counts mismatch: {residence_counts}")

    cs = SvgCoordinateSystem.from_file(COORD)
    OUT.mkdir(parents=True, exist_ok=True)
    for profile, path in OUTPUTS.items():
        path.write_text(render(profile, core, city_roads, wall, internal, water, cfg, rows, sports, policy, cs), encoding="utf-8")
        print(f"WROTE {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

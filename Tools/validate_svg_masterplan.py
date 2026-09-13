#!/usr/bin/env python3
import csv, json, sys
from pathlib import Path

EXPECTED_PATCH = "PATCH-2026-09-13-R6"

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def polygon_area(points):
    total = 0.0
    for (x1, z1), (x2, z2) in zip(points, points[1:] + points[:1]):
        total += x1 * z2 - x2 * z1
    return abs(total) / 2.0

def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def pos(row):
    def number(value):
        f = float(value)
        return int(f) if f.is_integer() else f
    return number(row["x"]), number(row["y"]), number(row["z"])

def main(root):
    root = Path(root)
    manifest = load_json(root / "CampusData/svg/masterplan_manifest_r6.json")
    core = load_json(root / "CampusData/svg/core_geometry_r6.json")
    external = load_json(root / "CampusData/transport/external_roads.json")
    wall = load_json(root / "CampusData/landscape/perimeter_wall.json")
    transport = load_json(root / "CampusData/svg/internal_roads_r3.json")
    water = load_json(root / "CampusData/svg/water_r6.json")
    sports = load_json(root / "CampusData/svg/outdoor_sports_r6.json")
    buildings = read_csv(root / "CampusData/svg/building_placement_r6.csv")

    errors = []
    def check(ok, message):
        if not ok:
            errors.append(message)

    for name, obj in (("manifest", manifest), ("core", core), ("external", external), ("wall", wall), ("transport", transport), ("water", water), ("sports", sports)):
        check(obj.get("sourcePatchVersion") == EXPECTED_PATCH, f"{name} patch != R6")

    area = polygon_area(core["campus"]["boundaryXZ"]) / 1e6
    check(abs(area - 6.5128) < 0.001, f"campus area {area:.4f}km² != 6.5128")

    expected_external = {
        "ROAD-CITY-SOUTH": "大学路",
        "ROAD-CITY-WEST": "学府路",
        "ROAD-CITY-NORTH": "致远路",
        "ROAD-CITY-EAST": "长虹路",
    }
    check(len(external["roads"]) == 4, "external road count != 4")
    check({r["id"]: r["name"] for r in external["roads"]} == expected_external, "external road IDs/names mismatch")
    check(external.get("geometryMode") == "piecewise_linear_with_corner_fillets", "external roads lost R6 straight-tangent mode")
    check(len(wall["segments"]) == 4, "wall segment count != 4")
    check(len(wall["openings"]) == 9, "wall opening count != 9")

    by = {row["id"]: row for row in buildings}
    residences = [row for row in buildings if row["id"].startswith("RES-")]
    check(len(buildings) == 204, f"building/facility records={len(buildings)} expected 204")
    check(len(residences) == 56, f"residence records={len(residences)} expected 56")
    check(by["HSP-02"]["groundFootprintIndependent"] == "False", "HSP-02 must not be independent ground footprint")
    check(by["HSP-02"]["parentBuildingID"] == "HSP-01", "HSP-02 parent must be HSP-01")
    check(pos(by["HSP-03"]) == (-1040, 99, -944), "HSP-03 not R6/R5 coordinate")
    check(pos(by["CSE-01"]) == (-760, 105, -120), "CSE-01 formal coordinate mismatch")
    for bid, expected in {
        "AERO-02": (-1090, 114, 640),
        "RDI-08": (-1080, 114, 740),
        "CEN-13": (-510, 101, 40),
        "AI-01": (-460, 105, 80),
        "NEE-01": (-470, 107, 280),
        "RDI-06": (-680, 114, 860),
    }.items():
        check(pos(by[bid]) == expected, f"{bid} R6 override mismatch")

    south_pond = next(x for x in water["waterBodies"] if x["id"] == "WATER-POND-SOUTH")
    check(south_pond["centerXZ"] == [600, -800], "south pond old coordinate leaked")
    check(abs(water["mainStream"]["visibleLengthApproxKm"] - 2.18) < 1e-9, "main stream baseline mismatch")

    road_map = {r["id"]: r for r in transport["internalRoads"]}
    check(len(transport["internalRoads"]) == 28, "internal road record count != 28")
    check(road_map["ROAD-BOYA-RING"]["centerlineXZ"][0] == [-830, -600], "Boya ring is not R3 chain")
    check(len(transport["busStops"]) == 22, "bus stop count != 22")
    check(len(transport["junctions"]) == 20, "junction count != 20")

    expected_totals = {
        "basketballFullCourtEquivalent": 44,
        "outdoorTableTennisTables": 158,
        "tennisCourts": 16,
        "volleyballCourts": 22,
        "outdoorBadmintonCourts": 16,
        "fiveASideFootballFields": 6,
    }
    check(sports["outdoorSportsTotals"] == expected_totals, "sports totals mismatch")
    check(len(sports["outdoorSports"]) == 36, "outdoor sport record count != 36")
    sport_map = {s["id"]: s for s in sports["outdoorSports"]}
    check(sport_map["ATH-14"]["position"] == {"x": 860, "y": 102, "z": -520}, "ATH-14 not R6 coordinate")
    check(sport_map["LIFE-S-BB-01"]["position"] == {"x": 250, "y": 100, "z": -620}, "South-life basketball not R6 coordinate")

    ids = []
    ids += [(r["id"], "externalRoads") for r in external["roads"]]
    ids += [(r["id"], "internalRoads") for r in transport["internalRoads"]]
    ids += [(x["id"], "entrances") for x in core["entrances"]]
    ids += [(x["id"], "outdoorSports") for x in sports["outdoorSports"]]
    ids += [(x["id"], "specialParcels") for x in core["specialParcels"]]
    ids += [(x["id"], "buildings") for x in buildings]
    seen = {}
    for object_id, family in ids:
        if object_id in seen:
            errors.append(f"duplicate drawable ID {object_id}: {seen[object_id]} / {family}")
        else:
            seen[object_id] = family

    for row in residences:
        if row["residenceType"] == "undergraduate":
            check(row["length"] == "" and row["footprintLengthMin"] == "78" and row["footprintLengthMax"] == "82", f"{row['id']} undergraduate footprint policy changed")

    print(f"PATCH={EXPECTED_PATCH}")
    print(f"CAMPUS_AREA={area:.4f}km²")
    print(f"BUILDING_OR_FACILITY_RECORDS={len(buildings)}")
    print(f"RESIDENCES={len(residences)}")
    print(f"EXTERNAL_ROADS={len(external['roads'])} INTERNAL_ROADS={len(transport['internalRoads'])}")
    print(f"BUS_STOPS={len(transport['busStops'])} JUNCTIONS={len(transport['junctions'])}")
    print(f"SPORT_OBJECTS={len(sports['outdoorSports'])}")
    if errors:
        for error in errors:
            print("FAIL", error)
        print(f"RESULT=FAIL errors={len(errors)}")
        return 1
    print("RESULT=PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))

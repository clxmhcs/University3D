#!/usr/bin/env python3
import csv, json, sys
from pathlib import Path

EXPECTED_PATCH='PATCH-2026-09-13-R6'

def polygon_area(points):
    a=0.0
    for (x1,z1),(x2,z2) in zip(points, points[1:]+points[:1]):
        a += x1*z2-x2*z1
    return abs(a)/2.0

def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def pos(row):
    def n(v):
        f=float(v); return int(f) if f.is_integer() else f
    return (n(row['x']),n(row['y']),n(row['z']))

def main(root):
    root=Path(root)
    m=json.loads((root/'CampusData/svg/masterplan_manifest_r6.json').read_text(encoding='utf-8'))
    g=json.loads((root/'CampusData/svg/masterplan_geometry_r6.json').read_text(encoding='utf-8'))
    b=read_csv(root/'CampusData/svg/building_placement_r6.csv')
    errors=[]
    def check(ok,msg):
        if not ok: errors.append(msg)

    check(m['sourcePatchVersion']==EXPECTED_PATCH,'manifest patch != R6')
    check(g['sourcePatchVersion']==EXPECTED_PATCH,'geometry patch != R6')
    area=polygon_area(g['campus']['boundaryXZ'])/1e6
    check(abs(area-6.5128)<0.001,f'campus area {area:.4f}km² != 6.5128')
    check(len(g['externalRoads'])==4,'external road count != 4')
    expected_roads={'ROAD-CITY-SOUTH':'大学路','ROAD-CITY-WEST':'学府路','ROAD-CITY-NORTH':'致远路','ROAD-CITY-EAST':'长虹路'}
    check({r['id']:r['name'] for r in g['externalRoads']}==expected_roads,'external road names/IDs mismatch')
    check(len(g['perimeterWall']['segments'])==4,'wall segment count != 4')
    check(len(g['perimeterWall']['openings'])==9,'wall opening count != 9')

    by={r['id']:r for r in b}
    res=[r for r in b if r['id'].startswith('RES-')]
    check(len(b)==204,f'building/facility records={len(b)} expected 204')
    check(len(res)==56,f'residence records={len(res)} expected 56')
    check(by['HSP-02']['groundFootprintIndependent']=='False','HSP-02 must not be independent ground footprint')
    check(by['HSP-02']['parentBuildingID']=='HSP-01','HSP-02 parent must be HSP-01')
    check(pos(by['HSP-03'])==(-1040,99,-944),'HSP-03 not R6/R5 coordinate')
    check(pos(by['CSE-01'])==(-760,105,-120),'CSE-01 formal coordinate mismatch')
    for bid,p in {'AERO-02':(-1090,114,640),'RDI-08':(-1080,114,740),'CEN-13':(-510,101,40),'AI-01':(-460,105,80),'NEE-01':(-470,107,280),'RDI-06':(-680,114,860)}.items():
        check(pos(by[bid])==p,f'{bid} R6 override mismatch')

    southpond=next(x for x in g['waterBodies'] if x['id']=='WATER-POND-SOUTH')
    check(southpond['centerXZ']==[600,-800],'south pond old coordinate leaked')
    check(abs(g['mainStream']['visibleLengthApproxKm']-2.18)<1e-9,'main stream baseline mismatch')
    roads={r['id']:r for r in g['internalRoads']}
    check(roads['ROAD-BOYA-RING']['centerlineXZ'][0]==[-830,-600],'Boya ring is not R3 chain')
    check(len(g['busStops'])==22,'bus stop count != 22')
    check(len(g['junctions'])==20,'junction count != 20')
    check(g['outdoorSportsTotals']=={'basketballFullCourtEquivalent':44,'outdoorTableTennisTables':158,'tennisCourts':16,'volleyballCourts':22,'outdoorBadmintonCourts':16,'fiveASideFootballFields':6},'sports totals mismatch')
    sm={s['id']:s for s in g['outdoorSports']}
    check(sm['ATH-14']['position']=={'x':860,'y':102,'z':-520},'ATH-14 not R6 coordinate')
    check(sm['LIFE-S-BB-01']['position']=={'x':250,'y':100,'z':-620},'South-life basketball not R6 coordinate')

    pairs=[]
    for family in ('externalRoads','internalRoads','entrances','outdoorSports','specialParcels'):
        pairs += [(x['id'],family) for x in g[family]]
    pairs += [(x['id'],'buildings') for x in b]
    seen={}
    for oid,fam in pairs:
        if oid in seen: errors.append(f'duplicate drawable ID {oid}: {seen[oid]} / {fam}')
        else: seen[oid]=fam

    for r in res:
        if r['residenceType']=='undergraduate':
            check(r['length']=='' and r['footprintLengthMin']=='78' and r['footprintLengthMax']=='82',f'{r["id"]} undergraduate footprint policy changed')

    print(f'PATCH={EXPECTED_PATCH}')
    print(f'CAMPUS_AREA={area:.4f}km²')
    print(f'BUILDING_OR_FACILITY_RECORDS={len(b)}')
    print(f'RESIDENCES={len(res)}')
    print(f'EXTERNAL_ROADS={len(g["externalRoads"])} INTERNAL_ROADS={len(g["internalRoads"])}')
    print(f'BUS_STOPS={len(g["busStops"])} JUNCTIONS={len(g["junctions"])}')
    print(f'SPORT_OBJECTS={len(g["outdoorSports"])}')
    if errors:
        for e in errors: print('FAIL',e)
        print(f'RESULT=FAIL errors={len(errors)}')
        return 1
    print('RESULT=PASS')
    return 0

if __name__=='__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv)>1 else '.'))

// R7-SOLVE-17. Audit-only grade and net-width gate.
// Node 22+, no dependencies. Does not issue fire, city-road or runtime approvals.
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

export const DEFAULT_PROFILE = 'CampusData/r7/solve_outputs/R7-SOLVE-17/R7-SOLVE-17_十一条路线10m高程与净宽测量待填表_2026-11-06.csv';

export function parseSourceCSV(content) {
  const lines = content.trimEnd().split(/\r?\n/).filter(Boolean);
  const matrix = lines.map((line, i) => {
    try { return line.split(',').map(v => JSON.parse(v)); }
    catch (error) { throw new Error('CSV_JSON_CELL_PARSE_FAILED_LINE_'+(i+1)+': '+error.message); }
  });
  const header = matrix.shift();
  if (!header || new Set(header).size !== header.length) throw new Error('INVALID_OR_DUPLICATE_HEADER');
  return matrix.map((values, i) => {
    if (values.length !== header.length) throw new Error('CSV_CELL_COUNT_WRONG_LINE_'+(i+2));
    return Object.fromEntries(header.map((name,j) => [name, values[j]]));
  });
}

const present = v => v !== null && v !== undefined && v !== '' && Number.isFinite(+v);

export function auditRows(rows) {
  const map = new Map(), problems = [], warnings = [], missing = {finishedY:0, surveyedY:0, netWidth:0, crossSlope:0};
  for (const row of rows) {
    if (!row.routeID) throw new Error('ROUTE_ID_REQUIRED');
    if (!present(row.chainage_m) || !present(row.x) || !present(row.z)) throw new Error('PROFILE_XZ_STATION_REQUIRED');
    if (row.runtimeFinal !== false && row.runtimeFinal !== 'false') problems.push({routeID:row.routeID,reason:'RUNTIME_FINAL_MUST_REMAIN_FALSE'});
    if (!map.has(row.routeID)) map.set(row.routeID,[]);
    map.get(row.routeID).push(row);
    if (!present(row.finishedRoadY_m)) missing.finishedY++;
    if (!present(row.surveyedRoadY_m)) missing.surveyedY++;
    if (!present(row.effectiveNetWidth_m)) missing.netWidth++;
    if (!present(row.crossSlope_pct)) missing.crossSlope++;
    if (present(row.effectiveNetWidth_m) && +row.effectiveNetWidth_m < 6) problems.push({routeID:row.routeID,chainage_m:row.chainage_m,reason:'NET_WIDTH_BELOW_6M',measured:+row.effectiveNetWidth_m});
  }
  let gradeIntervalsChecked=0,intervalsMissingY=0,profilesWithAllRoadY=0,profilesWithMeasuredNetWidth=0;
  for (const [routeID,part] of map) {
    part.sort((a,b)=>+a.chainage_m-(+b.chainage_m));
    const chainages=new Set();
    for (let i=0;i<part.length;i++) {
      let p=part[i],station=+p.chainage_m;
      if (chainages.has(station)) problems.push({routeID,chainage_m:station,reason:'DUPLICATE_STATION'});
      chainages.add(station);
      if (i===0) continue;
      let previous=part[i-1],distance=station-(+previous.chainage_m);
      if (distance<=0 || distance>10.02) problems.push({routeID,chainage_m:station,reason:'INVALID_SAMPLE_STATION_INTERVAL',distanceM:distance});
      if (!present(p.finishedRoadY_m) || !present(previous.finishedRoadY_m)) { intervalsMissingY++; continue; }
      let grade=Math.abs((+p.finishedRoadY_m)-(+previous.finishedRoadY_m))/distance*100;
      gradeIntervalsChecked++;
      if (grade>6+1e-8) problems.push({routeID,chainage_m:station,reason:'GRADE_EXCEEDS_6_PCT',gradePct:+grade.toFixed(3)});
      else if (grade>4+1e-8) warnings.push({routeID,chainage_m:station,reason:'GRADE_ABOVE_4_PCT_SPECIAL_REVIEW',gradePct:+grade.toFixed(3)});
    }
    if (part.every(p=>present(p.finishedRoadY_m)))profilesWithAllRoadY++;
    if (part.every(p=>present(p.effectiveNetWidth_m)))profilesWithMeasuredNetWidth++;
  }
  const completeProfiles=profilesWithAllRoadY===map.size&&profilesWithMeasuredNetWidth===map.size&&missing.surveyedY===0&&missing.crossSlope===0;
  return {status:problems.length?'GEOMETRY_PROFILE_SCREEN_ERROR':warnings.length?'GRADE_SPECIAL_REVIEW_REQUIRED':!completeProfiles?'BLOCKED_MISSING_MEASUREMENTS':'PROFILE_NUMERIC_PRECHECK_ONLY_NOT_FIRE_APPROVAL',
    auditAuthority:'PATCH-2026-09-14-R7',physicalFireApproval:false,runtimeFinal:false,
    sourceProfileRoutes:map.size,sampleStations:rows.length,gradeIntervalsChecked,intervalsMissingY,
    profilesWithAllRoadY,profilesWithMeasuredNetWidth,missing,problems,warnings,
    otherUnresolved:['realFireVehicleModel','actualTurnsAndSweeps','entranceDoorAndFireStaging','municipalGateAndWallRightOfWay','tenSmallPondTrueBanks','bridgeGeometryAndLoad']};
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const arg = process.argv.find(x=>x.startsWith('--input='));
  const filename = arg?arg.slice('--input='.length):DEFAULT_PROFILE;
  const result=auditRows(parseSourceCSV(fs.readFileSync(filename,'utf8')));
  console.log(JSON.stringify(result,null,2));
  if (process.argv.includes('--strict') && result.status !== 'PROFILE_NUMERIC_PRECHECK_ONLY_NOT_FIRE_APPROVAL') process.exitCode=2;
  else if (result.problems.length) process.exitCode=1;
}

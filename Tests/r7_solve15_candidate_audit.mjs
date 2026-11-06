// R7-SOLVE-15 regression checks; run at repository root: node Tests/r7_solve15_candidate_audit.mjs
import assert from 'node:assert/strict';
import fs from 'node:fs';
const load = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const base = 'CampusData/r7/solve_outputs/';
const id = base + 'R7-SOLVE-15/';
const data = load(id+'R7-SOLVE-15_五栋P0建筑消防侧向接入候选与审计_2026-11-06.json');
const geo = load(id+'R7-SOLVE-15_消防侧向接入候选空间_2026-11-06.geojson');
const old = load(base+'R7-SOLVE-14/R7-SOLVE-14_消防路网连通与195栋入口覆盖审计_2026-11-02.json');
const csv = fs.readFileSync(id+'R7-SOLVE-15_重点建筑消防道路净距候选表_2026-11-06.csv','utf8').trim().split(/\r?\n/);
const dist=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
const segDistance=(p,a,b)=>{
 const u=[b[0]-a[0],b[1]-a[1]];
 const n=u[0]*u[0]+u[1]*u[1];
 const t=n?Math.max(0,Math.min(1,((p[0]-a[0])*u[0]+(p[1]-a[1])*u[1])/n)):0;
 return dist(p,[a[0]+u[0]*t,a[1]+u[1]*t]);
};
assert.equal(data.solveId,'R7-SOLVE-15');
assert.equal(data.runtimeFinal,false);
assert.equal(data.results.length,6);
assert.equal(new Set(data.results.map(r=>r.buildingID)).size,5);
assert.deepEqual([...new Set(data.results.map(r=>r.buildingID))].sort(),
 ['ART-03','ATH-01','CEN-01','CEN-03','HSP-04']);
assert.equal(old.baseline.ordinaryMainEntranceCandidates,195);
assert.equal(old.coverage.with2DTieToGatewaySeedComponent,75);
assert.equal(old.coverage.withoutSource2DTie,120);
assert.equal(old.baseline.source11OriginalRiskCount,145);
assert.equal(data.originalBaseline.entrancesWithoutValidated2DTie,120);
assert.equal(data.originalBaseline.originalFireRisksStillOpen,145);
assert.equal(data.originalRisksClosed,0);
assert.equal(data.independentFireAccessApprovals,0);
assert.equal(csv.length,7);
assert.equal(geo.features.length,12);
for(const r of data.results){
 assert.equal(r.runtimeFinal,false);
 assert.equal(r.physicalFireApproval,false);
 assert.equal(r.originalRiskClosed,false);
 assert.equal(r.isBuildingMainEntrance,false);
 assert.equal(r.roadwayWidthM,8);
 assert.equal(r.nominalCenterlineObstacleSetbackRequiredM,7);
 assert.ok(r.sideStagingToTargetFootprintM>=7 && r.sideStagingToTargetFootprintM<=25);
 if(r.nearestOtherObstacle) assert.ok(r.nearestOtherObstacle.centerlineDistanceM>=7);
 if(r.nearestProtectedArea) assert.ok(r.nearestProtectedArea.centerlineDistanceM>=7);
 const centerline=r.centerlineXZ;
 const length=centerline.slice(1).reduce((s,p,i)=>s+dist(p,centerline[i]),0);
 assert.ok(Math.abs(length-r.lengthM)<0.02,r.id+' length mismatch');
 const road=old.selectedRoads.find(v=>v.id===r.anchorRoadID);
 assert.ok(road,r.id+' anchor road missing');
 assert.ok(road.graphComponentIds.includes('FIRE-COMP-01'));
 assert.ok(road.centerlineXZ.slice(1).some((p,i)=>segDistance(centerline[0],road.centerlineXZ[i],p)<0.01),r.id+' not connected on line');
 assert.equal(geo.features.filter(f=>f.properties.buildingID===r.buildingID).length,
 r.buildingID==='ATH-01'?4:2);
 const f=geo.features.find(x=>x.properties.id===r.id);
 assert.deepEqual(f.geometry.coordinates,centerline);
}
console.log('R7-SOLVE-15 candidate data invariants PASS (not fire vehicle certification)');

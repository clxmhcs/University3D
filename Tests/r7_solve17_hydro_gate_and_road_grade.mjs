import fs from 'node:fs';
import assert from 'node:assert/strict';
import {parseSourceCSV,auditRows} from '../Scripts/r7_solve17_elevation_clearance_gate.mjs';
(function checks(){
 const base='CampusData/r7/solve_outputs/';
 const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
 const a=read(base+'R7-SOLVE-17/R7-SOLVE-17_边界医院接口消防路线水系净距与高程证据_2026-11-06.json');
 const geo=read(base+'R7-SOLVE-17/R7-SOLVE-17_医院围墙边界与主水系候选审计空间_2026-11-06.geojson');
 const s15=read(base+'R7-SOLVE-15/R7-SOLVE-15_五栋P0建筑消防侧向接入候选与审计_2026-11-06.json');
 const s16geo=read(base+'R7-SOLVE-16/R7-SOLVE-16_消防车辆剧院回车与医院城市接口候选_2026-11-06.geojson');
 const testCSV='CampusData/r7/solve_outputs/R7-SOLVE-17/R7-SOLVE-17_十一条路线10m高程与净宽测量待填表_2026-11-06.csv';
 assert.equal(a.solveId,'R7-SOLVE-17'); assert.equal(a.runtimeFinal,false);
 assert.equal(a.authority,'PATCH-2026-09-14-R7');
 assert.equal(a.campusBoundarySource.verticesXZ.length,16);
 assert.equal(a.hospitalGateWallBoundaryAudit.length,2);
 assert.equal(a.P0WaterSourceControlScreening.length,7);
 assert.equal(a.officialHydrology.lakeWaterY,94);
 assert.equal(a.officialHydrology.northCreekFrozenControlXZ.length,10);
 assert.equal(a.officialHydrology.southeastCreekFrozenControlXZ.length,13);
 assert.equal(a.officialHydrology.shoreline13PointsXZ.length,13);
 assert.equal(a.officialHydrology.smallPondsCountWithoutActualPolygonBanks,10);
 assert.equal(a.physicalSafety.source145OriginalRisksClosed,0);
 assert.equal(a.physicalSafety.source14OrdinaryEntranceTotal,195);
 assert.equal(a.physicalSafety.source14Only2DCandidateGateTied,75);
 assert.equal(a.physicalSafety.source14Without2DTie,120);
 assert.equal(a.physicalSafety.successfulRuntimeFinalizations,0);
 assert.equal(a.roadProfileSpec.roadSlopeMeasurementCertifiedRouteCount,0);
 const B=a.campusBoundarySource.verticesXZ;
 const shoelace=Math.abs(B.reduce((x,p,i)=>{const q=B[(i+1)%B.length];return x+p[0]*q[1]-q[0]*p[1]},0)/2);
 assert.equal(shoelace,6512800);
 const delta=(a,b)=>[a[0]-b[0],a[1]-b[1]],dot=(a,b)=>a[0]*b[0]+a[1]*b[1],cross=(a,b)=>a[0]*b[1]-a[1]*b[0];
 const dist=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
 const pseg=(p,a,b)=>{let v=delta(b,a),den=dot(v,v),t=den?Math.max(0,Math.min(1,dot(delta(p,a),v)/den)):0;return dist(p,[a[0]+v[0]*t,a[1]+v[1]*t]);};
 const seg=(a,b,c,d)=>{
  let u=delta(b,a),v=delta(d,c),det=cross(u,v);
  if(Math.abs(det)>1e-9){let t=cross(delta(c,a),v)/det,s=cross(delta(c,a),u)/det;if(t>=0&&t<=1&&s>=0&&s<=1)return 0;}
  return Math.min(pseg(a,c,d),pseg(b,c,d),pseg(c,a,b),pseg(d,a,b));
 };
 const minSegments=(P,Q)=>{let min=Infinity;for(let i=1;i<P.length;i++)for(let j=1;j<Q.length;j++)min=Math.min(min,seg(P[i-1],P[i],Q[j-1],Q[j]));return min;};
 assert.equal(seg([0,0],[10,0],[5,-5],[5,5]),0);
 assert.equal(seg([0,0],[10,0],[0,10],[10,10]),10);
 assert.equal(seg([0,0],[10,0],[5,10],[5,20]),10);
 const N=a.officialHydrology.northCreekFrozenControlXZ,S=a.officialHydrology.southeastCreekFrozenControlXZ,L=a.officialHydrology.shoreline13PointsXZ;
 let waterChecks=0;
 for(const r of a.P0WaterSourceControlScreening){
  let stage=r.sourceStage==='R7-SOLVE-15'?s15.results.find(v=>v.id===r.routeID):null;
  let line=stage?.centerlineXZ??s16geo.features.find(f=>f.properties.id===r.routeID)?.geometry.coordinates;
  assert.ok(line,'Missing route '+r.routeID);
  assert.ok(Math.abs(minSegments(line,N)-r.northCreekCenterlineGapM)<0.02,r.routeID+' creek north distance drift');
  assert.ok(Math.abs(minSegments(line,S)-r.southeastCreekCenterlineGapM)<0.02,r.routeID+' creek south distance drift');
  assert.ok(Math.abs(minSegments(line,[...L,L[0]])-r.changhu13PointShorelineGapM)<0.02,r.routeID+' lake control drift');
  assert.equal(r.withinWaterControlScreeningRadius,false);
  assert.equal(r.actualRiverBankGeometryVerified,false);
  assert.equal(r.other10NamedPondShorelinesVerified,false);
  assert.equal(r.terrainGradeCertified,false);
  assert.equal(r.runtimeFinal,false);
  waterChecks++;
 }
 const southW=a.southWallSource.verticesXZ;
 function zAt(P,x){for(let i=1;i<P.length;i++){let [x0,z0]=P[i-1],[x1,z1]=P[i];if((x-x0)*(x-x1)<=0&&x0!==x1)return z0+(x-x0)/(x1-x0)*(z1-z0);}throw Error('X_OUT_OF_WALL_RANGE');}
 for(const h of a.hospitalGateWallBoundaryAudit){
  let x=h.officialEntranceXYZ[0],z=h.officialEntranceXYZ[2];
  assert.ok(Math.abs(zAt(B,x)-h.officialCampusBoundaryCrossingXZ[1])<0.001);
  assert.ok(Math.abs(zAt(southW,x)-h.officialSouthWallCrossingXZ[1])<0.001);
  assert.ok(Math.abs((z-zAt(B,x))-h.gateRelativeToCampusBoundarySouthIsNegativeM)<0.001);
  assert.ok(Math.abs((z-zAt(southW,x))-h.gateRelativeToWallSouthIsNegativeM)<0.001);
  assert.equal(h.wallCrossingApproval,false);
  assert.equal(h.noChangeToFrozenEntrance,true);
  assert.equal(h.officialCityRoadYMissing,true);
 }
 assert.equal(a.hospitalGateWallBoundaryAudit[0].gateRelativeToCampusBoundarySouthIsNegativeM<0,true);
 assert.equal(a.hospitalGateWallBoundaryAudit[1].gateRelativeToCampusBoundarySouthIsNegativeM>0,true);
 assert.ok(Math.abs(a.hospitalGateWallBoundaryAudit[0].twoFrozenEndpointNetGradePct-2.941)<0.01);
 assert.ok(Math.abs(a.hospitalGateWallBoundaryAudit[1].twoFrozenEndpointNetGradePct-1.064)<0.01);
 const rows=parseSourceCSV(fs.readFileSync(testCSV,'utf8'));
 assert.equal(rows.length,338);
 assert.equal(rows.length,a.roadProfileSpec.heightSamplesRequired);
 assert.equal(new Set(rows.map(r=>r.routeID)).size,11);
 assert.equal(geo.features.length,15);
 assert.equal(a.hospitalCityVehicleSweepScenarios.scenarios.length,4);
 assert.equal(a.hospitalCityVehicleSweepScenarios.scenariosCertifiedFireAccess,0);
 const actual=auditRows(rows);
 assert.equal(actual.status,'BLOCKED_MISSING_MEASUREMENTS');
 assert.equal(actual.gradeIntervalsChecked,0);
 assert.equal(actual.problems.length,0);
 assert.equal(actual.missing.finishedY,338);
 assert.equal(actual.missing.surveyedY,338);
 assert.equal(actual.missing.netWidth,338);
 assert.equal(actual.missing.crossSlope,338);
 assert.equal(actual.physicalFireApproval,false);
 const fixture=(dy,width=8)=>{
  const row=(x,y)=>({routeID:'SYNTHETIC_ONLY',chainage_m:x,x,z:0,surveyedRoadY_m:100,finishedRoadY_m:y,effectiveNetWidth_m:width,crossSlope_pct:2,runtimeFinal:false});
  return [row(0,100),row(10,100+dy)];
 };
 assert.equal(auditRows(fixture(0.3)).status,'PROFILE_NUMERIC_PRECHECK_ONLY_NOT_FIRE_APPROVAL');
 assert.equal(auditRows(fixture(0.5)).status,'GRADE_SPECIAL_REVIEW_REQUIRED');
 assert.equal(auditRows(fixture(0.7)).status,'GEOMETRY_PROFILE_SCREEN_ERROR');
 assert.equal(auditRows(fixture(0.3,5.9)).status,'GEOMETRY_PROFILE_SCREEN_ERROR');
 const missing=fixture(0.3);missing[1].finishedRoadY_m='';
 assert.equal(auditRows(missing).status,'BLOCKED_MISSING_MEASUREMENTS');
 const missingCross=fixture(0.3);missingCross[1].crossSlope_pct='';
 assert.equal(auditRows(missingCross).status,'BLOCKED_MISSING_MEASUREMENTS');
 console.log(JSON.stringify({result:'PASS_SOURCE_GEOMETRY_AND_NEGATIVE_GATES_NOT_FIRE_APPROVAL',
  waterSourceChecks:waterChecks,gateBoundaryChecks:2,sourceGradeProfiles:actual.sourceProfileRoutes,
  surveyStations:rows.length,certifiedGrades:0,originalRisksClosed:0}));
})();

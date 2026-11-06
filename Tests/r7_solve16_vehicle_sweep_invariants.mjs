import fs from 'node:fs';
import assert from 'node:assert/strict';
(function run(){
 const base="CampusData/r7/solve_outputs/";
 const read=p=>JSON.parse(fs.readFileSync(p,"utf8"));
 const d=read(base+"R7-SOLVE-16/R7-SOLVE-16_车辆扫掠医院剧院与高程水系审计_2026-11-06.json");
 const g=read(base+"R7-SOLVE-16/R7-SOLVE-16_消防车辆剧院回车与医院城市接口候选_2026-11-06.geojson");
 const s15=read(base+"R7-SOLVE-15/R7-SOLVE-15_五栋P0建筑消防侧向接入候选与审计_2026-11-06.json");
 const s14=read(base+"R7-SOLVE-14/R7-SOLVE-14_消防路网连通与195栋入口覆盖审计_2026-11-02.json");
 const hospital=read(base+"R7-SOLVE-12/R7-SOLVE-12_分区消防后勤道路候选与145项风险复核_2026-11-02.json");
 const csv=fs.readFileSync(base+"R7-SOLVE-16/R7-SOLVE-16_五栋P0消防车辆二维扫掠审计清单_2026-11-06.csv","utf8").trim().split(/\r?\n/);
 assert.equal(d.solveId,"R7-SOLVE-16");
 assert.equal(d.authority,"PATCH-2026-09-14-R7");
 assert.equal(d.runtimeFinal,false);
 assert.equal(d.auditScope.sourceFootprintCount,235);
 assert.equal(d.auditScope.protectedPolygonCount,8);
 assert.equal(d.routeCases.length,6);
 assert.equal(s15.results.length,6);
 assert.equal(csv.length,7);
 assert.equal(g.features.length,10);
 assert.equal(s14.coverage.with2DTieToGatewaySeedComponent,75);
 assert.equal(s14.coverage.withoutSource2DTie,120);
 assert.equal(s14.baseline.source11OriginalRiskCount,145);
 assert.equal(d.riskRegister.originalRisksClosedAfterStage16,0);
 assert.equal(d.riskRegister.stillUnlinkedMainEntrances,120);
 assert.equal(d.vehicleProxy.legalVehicleSpecification,false);
 assert.equal(d.hospital.sourceSixHospitalEntranceIDsRetained,true);
 assert.equal(d.hospital.cityConnectorLateralSpacingM,90);
 assert.equal(d.hospital.terminalAfterR12FilletStraightM,2);
 const hypot=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
 const dot=(a,b)=>a[0]*b[0]+a[1]*b[1];
 const sub=(a,b)=>[a[0]-b[0],a[1]-b[1]];
 const cross=(a,b)=>a[0]*b[1]-a[1]*b[0];
 const add=(a,b)=>[a[0]+b[0],a[1]+b[1]];
 const mult=(a,k)=>[a[0]*k,a[1]*k];
 const unit=a=>mult(a,1/Math.hypot(...a));
 const pointToSegment=(p,a,b)=>{
  let u=sub(b,a),t=Math.max(0,Math.min(1,dot(sub(p,a),u)/dot(u,u)));
  return hypot(p,add(a,mult(u,t)));
 };
 function fillet(path,R){
  let turns=[];
  for(let i=1;i<path.length-1;i++){
   const p=path[i],u=unit(sub(p,path[i-1])),v=unit(sub(path[i+1],p));
   const theta=Math.acos(Math.max(-1,Math.min(1,dot(u,v))));
   let t=R*Math.tan(theta/2);
   if(t>hypot(p,path[i-1])+1e-8||t>hypot(path[i+1],p)+1e-8)throw Error("Fillet tangent too long at "+i);
   turns.push({i,p,u,v,t,theta,sign:Math.sign(cross(u,v))});
  }
  for(let i=1;i<turns.length;i++)if(turns[i-1].t+turns[i].t>hypot(path[i+1],path[i])+1e-6)throw Error("Adjacent fillets overlap");
  const out=[path[0]];
  for(const r of turns){
   if(r.theta<1e-8){out.push(r.p);continue;}
   let p0=add(r.p,mult(r.u,-r.t));
   let p1=add(r.p,mult(r.v,r.t));
   let center=add(p0,mult([-r.u[1],r.u[0]],R*r.sign));
   let a0=Math.atan2(p0[1]-center[1],p0[0]-center[0]);
   let a1=Math.atan2(p1[1]-center[1],p1[0]-center[0]);
   if(r.sign>0)while(a1<=a0)a1+=2*Math.PI;
   else while(a1>=a0)a1-=2*Math.PI;
   out.push(p0);
   let n=Math.ceil(Math.abs(a1-a0)*R/0.7);
   for(let k=1;k<=n;k++)out.push(add(center,mult([Math.cos(a0+(a1-a0)*k/n),Math.sin(a0+(a1-a0)*k/n)],R)));
  }
  out.push(path.at(-1));
  return out;
 }
 const lineLength=p=>p.slice(1).reduce((v,x,i)=>v+hypot(x,p[i]),0);
 let testCount=0,approachCount=0;
 for(const rec of d.routeCases){
  const r=s15.results.find(v=>v.id===rec.id);
  assert.ok(r);
  const road=s14.selectedRoads.find(v=>v.id===r.anchorRoadID);
  assert.ok(road);
  assert.ok(road.graphComponentIds.includes("FIRE-COMP-01"));
  assert.equal(rec.physicalFireVehicleApproved,false);
  assert.equal(rec.runtimeFinal,false);
  assert.equal(rec.originalFireRiskClosed,false);
  assert.equal(rec.trueRoadGradeMeasured,false);
  assert.equal(rec.vehicleReturnOrTurnaroundCertified,false);
  const options=[];
  const start=r.centerlineXZ[0];
  for(let i=1;i<road.centerlineXZ.length;i++){
   let A=road.centerlineXZ[i-1],B=road.centerlineXZ[i];
   if(pointToSegment(start,A,B)>0.01)continue;
   for(const endpoint of [A,B]){
    if(hypot(endpoint,start)<25)continue;
    options.push([add(start,mult(unit(sub(endpoint,start)),25)),...r.centerlineXZ]);
   }
  }
  assert.equal(options.length,rec.sampledApproachOptions);
  for(const route of options){
   let rounded=fillet(route,12);
   assert.ok(rounded.length>=route.length);
   approachCount++;
  }
  assert.ok(Math.abs(lineLength(r.centerlineXZ)-r.lengthM)<0.02);
  testCount++;
 }
 const loop=g.features.find(v=>v.properties.id==="FIRE-R7S16-ART03-ONEWAY-RETURN-CANDIDATE");
 assert.ok(loop);
 assert.equal(loop.properties.runtimeFinal,false);
 assert.equal(loop.geometry.coordinates.length,121);
 assert.ok(Math.abs(lineLength(loop.geometry.coordinates)-259.09)<0.02);
 const s=hospital.candidateCorridors.find(v=>v.id==="ROAD-R7-S12-HSP-CITY-SOCIAL");
 const e=hospital.candidateCorridors.find(v=>v.id==="ROAD-R7-S12-HSP-CITY-AMBULANCE");
 const site=hospital.candidateCorridors.find(v=>v.id==="ROAD-R7-S12-HSP-ONSITE-AMBULANCE");
 assert.deepEqual(s.centerlineXZ,d.hospital.socialCityLinkXZ);
 assert.deepEqual(e.centerlineXZ,d.hospital.ambulanceCityLinkXZ);
 assert.deepEqual(site.centerlineXZ,d.hospital.onsiteAmbulanceLineXZ);
 assert.equal(Math.abs(s.centerlineXZ[0][0]-e.centerlineXZ[0][0]),90);
 assert.equal(site.centerlineXZ[2][0],-964);
 assert.equal(site.centerlineXZ[1][0],-950);
 assert.equal(Math.abs(site.centerlineXZ[2][0]-site.centerlineXZ[1][0])-12,2);
 for(const f of g.features)assert.equal(f.properties.runtimeFinal,false);
 console.log(JSON.stringify({result:"PASS_CANDIDATE_INVARIANTS_NOT_FIRE_APPROVAL",routes:testCount,entryApproaches:approachCount,source145RisksClosed:0,theatreLoopLengthM:259.09}));
})();

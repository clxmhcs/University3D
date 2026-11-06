import fs from 'node:fs';
import assert from 'node:assert/strict';
(function numericalCheck(){
 const root="CampusData/r7/solve_outputs/";
 const read=p=>JSON.parse(fs.readFileSync(p,"utf8"));
 const old=read(root+"R7-SOLVE-15/R7-SOLVE-15_五栋P0建筑消防侧向接入候选与审计_2026-11-06.json");
 const current=read(root+"R7-SOLVE-16/R7-SOLVE-16_车辆扫掠医院剧院与高程水系审计_2026-11-06.json");
 const graph=read(root+"R7-SOLVE-14/R7-SOLVE-14_消防路网连通与195栋入口覆盖审计_2026-11-02.json");
 const s01=read(root+"R7-SOLVE-01/R7-SOLVE-01_中央核心精确坐标候选解_2026-09-15.json");
 const s03=read(root+"R7-SOLVE-03/R7-SOLVE-03_西部工程信息学院组团候选解_2026-09-20.json");
 const s04=read(root+"R7-SOLVE-04/R7-SOLVE-04_东部人文社科经管学院组团候选解_2026-09-21.json");
 const s05=read(root+"R7-SOLVE-05/R7-SOLVE-05_四苑56栋住宿微观组团候选解_2026-11-01.json");
 const s06=read(root+"R7-SOLVE-06/R7-SOLVE-06_双体育中心附属场地与赛事交通候选解_2026-11-01.json");
 const protectedGeo=read(root+"R7-SOLVE-13/R7-SOLVE-13_中央核心四苑消防通道与保护区域空间候选_2026-11-02.geojson");
 const theatreGeo=read(root+"R7-SOLVE-16/R7-SOLVE-16_消防车辆剧院回车与医院城市接口候选_2026-11-06.geojson");
 const raw=fs.readFileSync("CampusData/svg/building_placement_r6.csv","utf8").trim().split(/\r?\n/);
 const columns=raw.shift().split(",");
 const original=raw.map(line=>Object.fromEntries(line.split(",").map((v,i)=>[columns[i],v])));
 const buildings=new Map();
 for(const r of original){
  if(r.id==="HSP-02"||!r.x||!r.z||!(+r.length>0)||!(+r.width>0))continue;
  buildings.set(r.id,{id:r.id,x:+r.x,z:+r.z,yaw:+r.rotationY,L:+r.length,W:+r.width});
 }
 function merge(r){
  const b=buildings.get(r.id)||{};
  const x=+(r.position?.[0]??r.x??b.x),z=+(r.position?.[2]??r.z??b.z);
  const L=+(r.footprintM?.[0]??r.auditLength??r.length??r.L??b.L);
  const W=+(r.footprintM?.[1]??r.auditWidth??r.width??r.W??b.W);
  const yaw=+(r.rotationY??b.yaw??0);
  if(r.id&&Number.isFinite(x)&&Number.isFinite(z)&&L>0&&W>0)buildings.set(r.id,{id:r.id,x,z,yaw,L,W});
 }
 for(const [id,r] of Object.entries(s01.buildingCandidates))merge({...r,id});
 for(const r of s03.buildings)merge(r);
 for(const r of s04.buildings)merge(r);
 for(const r of [...s05.residences,...s05.lifeServices,...s05.sports])merge(r);
 for(const r of [...s06.frozenAnchors,...s06.sportFields,...s06.ancillaryFacilities])if(r.category!=="open_plaza")merge(r);
 buildings.delete("ATH-02");
 assert.equal(buildings.size,235);
 const mul=(a,k)=>[a[0]*k,a[1]*k],add=(a,b)=>[a[0]+b[0],a[1]+b[1]],sub=(a,b)=>[a[0]-b[0],a[1]-b[1]];
 const norm=a=>Math.hypot(...a),unit=a=>mul(a,1/norm(a));
 const dd=(a,b)=>norm(sub(a,b)),dot=(a,b)=>a[0]*b[0]+a[1]*b[1],cross=(a,b)=>a[0]*b[1]-a[1]*b[0];
 function rect(v){
  const c=Math.cos(v.yaw*Math.PI/180),s=Math.sin(v.yaw*Math.PI/180);
  return [[-1,-1],[1,-1],[1,1],[-1,1]].map(([a,b])=>[v.x+a*v.L*c/2-b*v.W*s/2,v.z+a*v.L*s/2+b*v.W*c/2]);
 }
 const footprints=[...buildings.values()].map(v=>({id:v.id,polygon:rect(v)}));
 const protectedAreas=protectedGeo.features.filter(f=>f.geometry.type==="Polygon").map(v=>({id:v.properties.id,polygon:v.geometry.coordinates[0].slice(0,-1)}));
 assert.equal(protectedAreas.length,8);
 function pointToSeg(p,a,b){
  let u=sub(b,a),n=dot(u,u),t=n?Math.max(0,Math.min(1,dot(sub(p,a),u)/n)):0;
  return dd(p,add(a,mul(u,t)));
 }
 function inside(pt,P){
  let yes=false;
  for(let i=0,j=P.length-1;i<P.length;j=i++){
   let a=P[i],b=P[j];
   if((a[1]>pt[1])!==(b[1]>pt[1])&&pt[0]<(b[0]-a[0])*(pt[1]-a[1])/(b[1]-a[1])+a[0])yes=!yes;
  }
  return yes;
 }
 function segmentHit(a,b,c,e){
  const u=sub(b,a),v=sub(e,c),det=cross(u,v);
  if(Math.abs(det)<1e-9)return Math.min(pointToSeg(a,c,e),pointToSeg(b,c,e),pointToSeg(c,a,b),pointToSeg(e,a,b))<1e-7;
  const t=cross(sub(c,a),v)/det,s=cross(sub(c,a),u)/det;
  return t>=-1e-9&&t<=1+1e-9&&s>=-1e-9&&s<=1+1e-9;
 }
 function polyGap(A,B){
  if(A.some(p=>inside(p,B))||B.some(p=>inside(p,A)))return 0;
  let minimum=Infinity;
  for(let i=0;i<A.length;i++){
   let a=A[i],b=A[(i+1)%A.length];
   for(let j=0;j<B.length;j++){
    let c=B[j],e=B[(j+1)%B.length];
    if(segmentHit(a,b,c,e))return 0;
    minimum=Math.min(minimum,pointToSeg(a,c,e),pointToSeg(b,c,e),pointToSeg(c,a,b),pointToSeg(e,a,b));
   }
  }
  return minimum;
 }
 function rounded(P,R){
  let bends=[],issues=[];
  for(let i=1;i<P.length-1;i++){
   const u=unit(sub(P[i],P[i-1])),v=unit(sub(P[i+1],P[i]));
   const theta=Math.acos(Math.max(-1,Math.min(1,dot(u,v)))),t=R*Math.tan(theta/2);
   bends.push({i,p:P[i],u,v,theta,t,sign:Math.sign(cross(u,v))});
   if(t>dd(P[i],P[i-1])+1e-9||t>dd(P[i+1],P[i])+1e-9)issues.push("SHORT_SEGMENT_"+i);
  }
  for(let i=1;i<bends.length;i++)if(bends[i-1].t+bends[i].t>dd(P[i+1],P[i])+1e-9)issues.push("OVERLAP_"+i);
  if(issues.length)throw Error("Radius12 cannot fit: "+issues.join(","));
  const out=[P[0]];
  for(const r of bends){
   if(r.theta<1e-8){out.push(r.p);continue;}
   let before=add(r.p,mul(r.u,-r.t)),after=add(r.p,mul(r.v,r.t));
   let center=add(before,mul([-r.u[1],r.u[0]],R*r.sign));
   let a0=Math.atan2(before[1]-center[1],before[0]-center[0]),a1=Math.atan2(after[1]-center[1],after[0]-center[0]);
   if(r.sign>0)while(a1<=a0)a1+=Math.PI*2;else while(a1>=a0)a1-=Math.PI*2;
   out.push(before);
   let n=Math.ceil(Math.abs(a1-a0)*R/0.7);
   for(let k=1;k<=n;k++)out.push(add(center,mul([Math.cos(a0+(a1-a0)*k/n),Math.sin(a0+(a1-a0)*k/n)],R)));
  }
  out.push(P.at(-1));
  return out;
 }
 function swept(P){
  let F=[P[0]];
  for(let i=1;i<P.length;i++){
   let n=Math.max(1,Math.ceil(dd(P[i],P[i-1])/0.7));
   for(let j=1;j<=n;j++)F.push(add(P[i-1],mul(sub(P[i],P[i-1]),j/n)));
  }
  const poses=[];
  let rear=add(F[0],mul(unit(sub(F[1],F[0])),-6.7));
  for(let i=0;i<F.length;i++){
   let front=F[i];
   if(i>0){
    let u=unit(sub(F[i-1],rear)),delta=sub(front,F[i-1]);
    let guess=add(rear,mul(u,dot(delta,u)));
    rear=add(front,mul(unit(sub(front,guess)),-6.7));
   }
   let direction=unit(sub(front,rear)),side=[-direction[1],direction[0]];
   let back=add(rear,mul(direction,-2.8)),head=add(rear,mul(direction,9.2));
   poses.push([add(back,mul(side,-1.275)),add(head,mul(side,-1.275)),add(head,mul(side,1.275)),add(back,mul(side,1.275))]);
  }
  return poses;
 }
 function metrics(path){
  let minX=Math.min(...path.map(p=>p[0]))-25,maxX=Math.max(...path.map(p=>p[0]))+25;
  let minZ=Math.min(...path.map(p=>p[1]))-25,maxZ=Math.max(...path.map(p=>p[1]))+25;
  let nearby=footprints.filter(f=>f.polygon.some(p=>p[0]>=minX-150&&p[0]<=maxX+150&&p[1]>=minZ-150&&p[1]<=maxZ+150));
  let bestBuilding=Infinity,bestProtected=Infinity;
  for(const pose of swept(path)){
   for(const f of nearby)bestBuilding=Math.min(bestBuilding,polyGap(pose,f.polygon));
   for(const p of protectedAreas)bestProtected=Math.min(bestProtected,polyGap(pose,p.polygon));
  }
  return [bestBuilding,bestProtected];
 }
 let simulationCount=0;
 for(const rec of current.routeCases){
  const r=old.results.find(x=>x.id===rec.id);
  const parent=graph.selectedRoads.find(x=>x.id===r.anchorRoadID);
  const start=r.centerlineXZ[0];
  const options=[];
  for(let i=1;i<parent.centerlineXZ.length;i++){
   let a=parent.centerlineXZ[i-1],b=parent.centerlineXZ[i];
   if(pointToSeg(start,a,b)>0.001)continue;
   for(const endpoint of [a,b]){
    if(dd(endpoint,start)>=25)options.push([add(start,mul(unit(sub(endpoint,start)),25)),...r.centerlineXZ]);
   }
  }
  assert.equal(options.length,rec.sampledApproachOptions);
  for(let i=0;i<options.length;i++){
   const values=metrics(rounded(options[i],12));
   const expected=[rec.closestBodyToKnownFootprintByApproachM[i],rec.closestBodyToProtectedByApproachM[i]];
   assert.ok(Math.abs(values[0]-expected[0])<0.15,rec.id+" building sweep "+values[0]+" expected "+expected[0]);
   assert.ok(Math.abs(values[1]-expected[1])<0.15,rec.id+" protected sweep "+values[1]+" expected "+expected[1]);
   assert.ok(values[0]>0&&values[1]>0,rec.id+" geometry proxy overlap");
   simulationCount++;
  }
 }
 const loop=theatreGeo.features.find(f=>f.properties.id==="FIRE-R7S16-ART03-ONEWAY-RETURN-CANDIDATE");
 assert.ok(loop);
 const result=metrics(loop.geometry.coordinates);
 console.log(JSON.stringify({numericSimulation:"PASS_FOR_SOURCE_ENVELOPES_NOT_FIRE_APPROVAL",bodySweepCases:simulationCount,sourceBuildingFootprints:footprints.length,protectedPolygons:protectedAreas.length,theatreReturnLoopMinKnownBuildingM:+result[0].toFixed(2),theatreReturnLoopMinKnownProtectedM:+result[1].toFixed(2)}));
})();

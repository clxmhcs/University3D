import fs from 'node:fs';
import assert from 'node:assert/strict';
(function replay(){
 const base='CampusData/r7/solve_outputs/R7-SOLVE-17/';
 const data=JSON.parse(fs.readFileSync(base+'R7-SOLVE-17_边界医院接口消防路线水系净距与高程证据_2026-11-06.json','utf8'));
 const source=data.hospitalCityVehicleSweepScenarios;
 assert.equal(source.scenarios.length,4);
 const sub=(a,b)=>[a[0]-b[0],a[1]-b[1]],add=(a,b)=>[a[0]+b[0],a[1]+b[1]],mult=(a,x)=>[a[0]*x,a[1]*x];
 const length=a=>Math.hypot(a[0],a[1]),unit=a=>mult(a,1/length(a)),d=(a,b)=>length(sub(a,b)),dot=(a,b)=>a[0]*b[0]+a[1]*b[1],cross=(a,b)=>a[0]*b[1]-a[1]*b[0];
 function rounded(P,R){
  let bend=[];
  for(let i=1;i<P.length-1;i++){
   const u=unit(sub(P[i],P[i-1])),v=unit(sub(P[i+1],P[i]));
   const theta=Math.acos(Math.min(1,Math.max(-1,dot(u,v)))),t=R*Math.tan(theta/2);
   assert.ok(t<=d(P[i],P[i-1])+1e-8&&t<=d(P[i+1],P[i])+1e-8,'Unfit tangent');
   bend.push({p:P[i],u,v,theta,t,sg:Math.sign(cross(u,v))});
  }
  for(let i=1;i<bend.length;i++)assert.ok(bend[i-1].t+bend[i].t<=d(P[i+1],P[i])+1e-8,'Overlap');
  let path=[P[0]];
  for(const b of bend){
   if(b.theta<1e-8){path.push(b.p);continue;}
   const pre=add(b.p,mult(b.u,-b.t)),post=add(b.p,mult(b.v,b.t));
   const cen=add(pre,mult([-b.u[1],b.u[0]],R*b.sg));
   let a0=Math.atan2(pre[1]-cen[1],pre[0]-cen[0]),a1=Math.atan2(post[1]-cen[1],post[0]-cen[0]);
   if(b.sg>0)while(a1<=a0)a1+=2*Math.PI;else while(a1>=a0)a1-=2*Math.PI;
   const n=Math.ceil(Math.abs(a1-a0)*R/0.7);path.push(pre);
   for(let k=1;k<=n;k++){const ang=a0+(a1-a0)*k/n;path.push(add(cen,mult([Math.cos(ang),Math.sin(ang)],R)));}
  }
  return [...path,P.at(-1)];
 }
 function vehicle(P){
  let center=[P[0]];
  for(let i=1;i<P.length;i++){
   let count=Math.max(1,Math.ceil(d(P[i],P[i-1])/0.7));
   for(let j=1;j<=count;j++)center.push(add(P[i-1],mult(sub(P[i],P[i-1]),j/count)));
  }
  let rear=add(center[0],mult(unit(sub(center[1],center[0])),-6.7)),out=[];
  for(let i=0;i<center.length;i++){
   const front=center[i];
   if(i>0){const u=unit(sub(center[i-1],rear)),move=sub(front,center[i-1]),guess=add(rear,mult(u,dot(move,u)));rear=add(front,mult(unit(sub(front,guess)),-6.7));}
   let direction=unit(sub(front,rear)),l=[-direction[1],direction[0]];
   const back=add(rear,mult(direction,-2.8)),head=add(rear,mult(direction,9.2));
   out.push({front,corners:[add(back,mult(l,-1.275)),add(head,mult(l,-1.275)),add(head,mult(l,1.275)),add(back,mult(l,1.275))]});
  }
  return out;
 }
 const bld=[[-1110,-1045],[-970,-1045],[-970,-975],[-1110,-975]];
 function inside(p,P){let yes=false;for(let i=0,j=P.length-1;i<P.length;j=i++){let a=P[i],b=P[j];if((a[1]>p[1])!==(b[1]>p[1]) && p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])yes=!yes;}return yes;}
 function pSeg(p,a,b){const v=sub(b,a),den=dot(v,v),t=den?Math.max(0,Math.min(1,dot(sub(p,a),v)/den)):0;return d(p,add(a,mult(v,t)));}
 function polyGap(A,B){
  if(A.some(p=>inside(p,B))||B.some(p=>inside(p,A)))return 0;
  let best=Infinity;
  for(let i=0;i<A.length;i++)for(let j=0;j<B.length;j++){
   const a=A[i],b=A[(i+1)%A.length],c=B[j],e=B[(j+1)%B.length];
   const u=sub(b,a),v=sub(e,c),det=cross(u,v);
   if(Math.abs(det)>1e-8){const t=cross(sub(c,a),v)/det,s=cross(sub(c,a),u)/det;if(t>=0&&t<=1&&s>=0&&s<=1)return 0;}
   best=Math.min(best,pSeg(a,c,e),pSeg(b,c,e),pSeg(c,a,b),pSeg(e,a,b));
  }
  return best;
 }
 let minGap=Infinity;
 for(const sc of source.scenarios){
  const expected=data.hospitalGateWallBoundaryAudit.find(x=>x.entryID===sc.gateID);
  assert.ok(expected);
  const x=expected.officialEntranceXYZ[0],z=expected.officialEntranceXYZ[2];
  assert.deepEqual(sc.controlCenterlineXZ[1],[x,-1145]);
  assert.deepEqual(sc.controlCenterlineXZ[2],[x,-1127]);
  assert.deepEqual(sc.controlCenterlineXZ[3],[x,z]);
  assert.equal(sc.sourceActualLaneDirectionNotConfirmed,true);
  assert.equal(sc.municipalTurningRightOfWayApproved,false);
  assert.equal(sc.fireAccessCertified,false);
  assert.equal(sc.runtimeFinal,false);
  let poses=vehicle(rounded(sc.controlCenterlineXZ,12));
  assert.equal(poses.length,sc.sampledBodyPoses);
  const clearance=Math.min(...poses.map(x=>polyGap(x.corners,bld)));
  minGap=Math.min(minGap,clearance);
  assert.ok(Math.abs(clearance-sc.minBodyToFrozenHSP01FootprintM)<0.04,sc.gateID+' HSP01 gap '+clearance);
  let atGate=poses.filter(p=>Math.abs(p.front[1]-z)<1);
  let atWall=poses.filter(p=>Math.abs(p.front[1]-expected.officialSouthWallCrossingXZ[1])<1);
  assert.ok(atGate.length>0&&atWall.length>0);
  let g=Math.max(...atGate.flatMap(p=>p.corners.map(q=>Math.abs(q[0]-x))));
  let w=Math.max(...atWall.flatMap(p=>p.corners.map(q=>Math.abs(q[0]-x))));
  assert.ok(Math.abs(g-sc.maxBodyLateralDeviationAtFrozenGateM)<0.05);
  assert.ok(Math.abs(w-sc.maxBodyLateralDeviationAtWallProjectionM)<0.05);
  assert.ok(g<=sc.sourceFrozenWallOpeningWidthM/2&&w<=sc.sourceFrozenWallOpeningWidthM/2);
  assert.ok(g>1,'NARROW_2M_SYNTHETIC_OPENING_WOULD_NOT_PASS');
  assert.equal(sc.actualTruckDynamicsCertified,false);
 }
 assert.equal(source.scenariosCertifiedFireAccess,0);
 console.log(JSON.stringify({result:'PASS_HYPOTHETICAL_CITY_TURNS_NOT_MUNICIPAL_FIRE_CERTIFICATION',cases:4,minHSP01BodyGapM:+minGap.toFixed(3),officialHospitalGateIDs:2,certified:0}));
})();

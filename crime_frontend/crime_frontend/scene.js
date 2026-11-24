import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js';
// All geometry is original. Scene position is never new evidence.
let setup=false;
function boot(){
 if(setup||!window.caseSceneConfig)return;setup=true;
 try{
 const kind=window.caseSceneConfig.scene_id||'hotel',stage=document.querySelector('#stage');
 const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'low-power'});
 renderer.setPixelRatio(Math.min(devicePixelRatio,1.6));renderer.shadowMap.enabled=true;
 renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputColorSpace=THREE.SRGBColorSpace;
 const sky=kind==='hotel'?0x15221e:kind==='hankorab'?0x101e32:0x142433;
 renderer.setClearColor(sky);stage.prepend(renderer.domElement);
 const scene=new THREE.Scene();scene.fog=new THREE.Fog(sky,22,65);
 const camera=new THREE.PerspectiveCamera(46,1,.1,130);
 let angle=kind==='hankorab'?-.18:.55,elev=kind==='hankorab'?.68:.55,radius=kind==='hotel'?10:17;
 const initial={angle,elev,radius},target=new THREE.Vector3(0,kind==='hotel'?1:1.2,0);
 function cam(){camera.position.set(Math.sin(angle)*radius,1+Math.sin(elev)*radius,Math.cos(angle)*radius);camera.lookAt(target)}cam();
 const mat=(c,r=.82,m=0)=>new THREE.MeshStandardMaterial({color:c,roughness:r,metalness:m});
 const sand=mat(0xc3ad79),wood=mat(0x64503a),dark=mat(0x25251f),green=mat(0x314f42),brass=mat(0xbc9a53,.4,.5),paper=mat(0xe3d4ad),blue=mat(0x376b87,.35);
 const objects=[];
 function mesh(g,m,x=0,y=0,z=0){const o=new THREE.Mesh(g,m);o.position.set(x,y,z);o.castShadow=true;o.receiveShadow=true;scene.add(o);return o}
 const box=(w,h,d,m,x,y,z)=>mesh(new THREE.BoxGeometry(w,h,d),m,x,y,z);
 const cyl=(a,b,h,m,x,y,z,n=24)=>mesh(new THREE.CylinderGeometry(a,b,h,n),m,x,y,z);
 const tag=(o,id)=>{o.userData.file=id;objects.push(o);return o};
 function textLabel(text,x,y,z,width=1){const c=document.createElement('canvas');c.width=256;c.height=96;const ctx=c.getContext('2d');ctx.fillStyle='#e5d7b8';ctx.fillRect(0,0,256,96);ctx.fillStyle='#233f35';ctx.font='bold 42px sans-serif';ctx.textAlign='center';ctx.fillText(text,128,64);const o=mesh(new THREE.PlaneGeometry(width,width*.375),new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(c),side:THREE.DoubleSide}),x,y,z);return o}
 function packet(id,x,y,z){tag(box(.72,.07,.52,paper,x,y,z),id);let t=tag(textLabel(id,x,y+.04,z,.65),id);t.rotation.x=-Math.PI/2}
 function lamp(x,y,z){cyl(.18,.22,.08,brass,x,y,z);cyl(.04,.04,.7,brass,x,y+.4,z);cyl(.24,.28,.35,mat(0xdfb55b,.6),x,y+.65,z);const p=new THREE.PointLight(0xffb34f,18,7,2);p.position.set(x,y+.8,z);scene.add(p)}

 // Non-graphic crime scene: sheet-covered victim, chalk outline, numbered markers and tape. Position is never evidence.
 function crimeScene(cx,fy,cz,rot){
  const g=new THREE.Group();g.position.set(cx,fy,cz);g.rotation.y=rot;scene.add(g);
  const add=(o)=>{o.castShadow=true;o.receiveShadow=true;g.add(o);return o};
  const c=document.createElement('canvas');c.width=256;c.height=384;const x=c.getContext('2d');x.clearRect(0,0,256,384);x.strokeStyle='#f4f1e6';x.lineWidth=7;x.lineJoin='round';
  x.beginPath();x.arc(128,52,32,0,7);x.stroke();x.beginPath();x.moveTo(98,92);x.lineTo(60,120);x.lineTo(30,230);x.moveTo(158,92);x.lineTo(196,120);x.lineTo(226,200);x.moveTo(98,92);x.lineTo(158,92);x.lineTo(150,210);x.lineTo(168,350);x.moveTo(106,210);x.lineTo(88,350);x.moveTo(106,210);x.lineTo(150,210);x.stroke();
  const outline=new THREE.Mesh(new THREE.PlaneGeometry(1.9,2.85),new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(c),transparent:true,depthWrite:false}));outline.rotation.x=-Math.PI/2;outline.position.y=.012;g.add(outline);
  const sheet=new THREE.MeshStandardMaterial({color:0xeceee8,roughness:1});
  // One draped cloth over the whole body: long low mound with soft peaks at head, shoulders and feet.
  const mound=add(new THREE.Mesh(new THREE.SphereGeometry(1,24,14),sheet));mound.scale.set(.36,.14,1.2);mound.position.set(0,.05,0);
  // head, shoulders, hips, feet under the cloth
  [[0,-.98,.12,.17,.17],[0,-.55,.14,.3,.2],[0,.05,.11,.26,.2],[-.11,.95,.08,.1,.16],[.11,.95,.08,.1,.16]].forEach(([px,pz,h,rx,rz])=>{const k=add(new THREE.Mesh(new THREE.SphereGeometry(1,14,10),sheet));k.scale.set(rx,h,rz);k.position.set(px,.1+h*.4,pz)});
  const edge=add(new THREE.Mesh(new THREE.TorusGeometry(.5,.012,6,32),new THREE.MeshStandardMaterial({color:0xb9c1c4,roughness:1})));edge.rotation.x=Math.PI/2;edge.scale.set(.85,2.1,1);edge.position.y=.03;
  const yellow=new THREE.MeshStandardMaterial({color:0xf2c230,roughness:.6});
  [[-1.1,-.4,'1'],[1.15,.5,'2'],[.9,-1.0,'3']].forEach(([mx,mz,n])=>{const t=add(new THREE.Mesh(new THREE.ConeGeometry(.12,.3,4),yellow));t.position.set(mx,.15,mz);const lc=document.createElement('canvas');lc.width=64;lc.height=64;const lx=lc.getContext('2d');lx.fillStyle='#f2c230';lx.fillRect(0,0,64,64);lx.fillStyle='#1d1d18';lx.font='bold 44px sans-serif';lx.textAlign='center';lx.fillText(n,32,48);const l=new THREE.Mesh(new THREE.PlaneGeometry(.22,.22),new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(lc)}));l.position.set(mx,.34,mz);l.rotation.x=-.5;g.add(l)});
  const tapeM=new THREE.MeshBasicMaterial({color:0xf2c230});const post=new THREE.MeshStandardMaterial({color:0x2a2a25});
  const P=[[-1.6,-1.7],[1.6,-1.7],[1.6,1.7],[-1.6,1.7]];
  P.forEach(([px,pz])=>{const p=add(new THREE.Mesh(new THREE.CylinderGeometry(.035,.035,.8,8),post));p.position.set(px,.4,pz)});
  for(let i=0;i<4;i++){const a=P[i],b=P[(i+1)%4];const len=Math.hypot(b[0]-a[0],b[1]-a[1]);const t=new THREE.Mesh(new THREE.BoxGeometry(len,.07,.008),tapeM);t.position.set((a[0]+b[0])/2,.68,(a[1]+b[1])/2);t.rotation.y=-Math.atan2(b[1]-a[1],b[0]-a[0]);g.add(t)}
 }
 scene.add(new THREE.HemisphereLight(kind==='hankorab'?0x91bce8:0xc3d2d4,0x373327,1.7));
 const key=new THREE.DirectionalLight(0xc3dbf0,2);key.position.set(5,10,4);key.castShadow=true;key.shadow.mapSize.set(1024,1024);key.shadow.camera.left=-12;key.shadow.camera.right=12;key.shadow.camera.top=12;key.shadow.camera.bottom=-12;scene.add(key);
 const animated=[];
 if(kind!=='hotel'){
  const stars=[];let seed=171;for(let i=0;i<170;i++){seed=(seed*16807)%2147483647;let a=seed/2147483647*Math.PI*2;seed=(seed*16807)%2147483647;let h=.1+seed/2147483647*.85;stars.push(Math.cos(a)*48,10+h*35,Math.sin(a)*48)}
  let g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(stars,3));scene.add(new THREE.Points(g,new THREE.PointsMaterial({color:0xcddce3,size:.09})));
  const moon=mesh(new THREE.SphereGeometry(1,24,16),new THREE.MeshBasicMaterial({color:0xf0e6c8}),-20,22,-34);
  const water=mesh(new THREE.PlaneGeometry(100,100,40,40),new THREE.MeshStandardMaterial({color:kind==='hankorab'?0x194358:0x203d4c,roughness:.35,metalness:.35}),0,-.22,-22);water.rotation.x=-Math.PI/2;
  for(let i=0;i<25;i++){let wave=box(1+(i%5)*.5,.015,.035,new THREE.MeshBasicMaterial({color:0x75979b,transparent:true,opacity:.3}),Math.sin(i*2)*18,-.17,-9-i*1.2);animated.push(wave)}
 }
 if(kind==='hotel'){
  box(11,.16,9,mat(0x74674f),0,-.1,0);box(11,4.7,.15,green,0,2.25,-4.5);box(.15,4.7,9,green,-5.5,2.25,0);
  for(let x=-5;x<5;x+=1.2)box(.035,2.2,.09,brass,x,1.2,-4.38);
  box(2.2,3.5,.15,dark,-3.5,1.75,-4.35);box(1.95,3.25,.16,wood,-3.5,1.65,-4.23);cyl(.08,.08,.1,brass,-2.8,1.6,-4.1).rotation.x=Math.PI/2;
  box(2.9,2.9,.18,dark,2.8,2.8,-4.34);box(2.6,2.6,.18,mat(0x314d59),2.8,2.8,-4.22);box(.1,2.6,.2,brass,2.8,2.8,-4.1);box(2.6,.1,.2,brass,2.8,2.8,-4.1);
  box(7,.015,5,mat(0x6b4e3a),0,.02,.5);box(6.6,.02,4.6,green,0,.04,.5);
  box(5,.2,2.6,wood,0,1.5,.3);for(let x of [-2.1,2.1])for(let z of [-.65,1.25])box(.17,1.5,.17,dark,x,.7,z);
  box(1.5,.15,1.5,green,0,.7,-2);box(1.5,1.6,.2,green,0,1.5,-2.65);lamp(-1.6,1.65,0);
  tag(cyl(.23,.18,.4,blue,.8,1.82,.8),'E07');let handle=tag(mesh(new THREE.TorusGeometry(.15,.035,8,20),blue,1.04,1.82,.8),'E07');handle.rotation.y=Math.PI/2;tag(cyl(.36,.36,.03,paper,.8,1.62,.8),'E07');
  tag(cyl(.28,.28,.08,brass,1.6,1.68,.2),'E05');tag(cyl(.24,.24,.01,paper,1.6,1.73,.2),'E05');tag(box(.025,.01,.17,dark,1.6,1.74,.15),'E05');
  tag(box(.85,.18,.6,dark,-.25,1.73,-.1),'E03');tag(cyl(.21,.21,.03,brass,-.25,1.84,-.05),'E03');tag(box(.95,.12,.14,dark,-.25,1.96,-.25),'E03');packet('E01',-.7,1.64,1);
  ['E02','E04','E06','E08','E09'].forEach((id,i)=>packet(id,-2+i*.85,.18,2.0));
 }else if(kind==='hankorab'){
  box(27,.3,18,sand,0,-.2,2);const tentMat=mat(0xb78d50),tentDark=mat(0x493e33);
  function tent(x,z,rotation=0){const group=new THREE.Group();const points=new Float32Array([-1.7,0,-1.6,1.7,0,-1.6,0,2,-1.6,-1.7,0,1.6,0,2,1.6,1.7,0,1.6,-1.7,0,-1.6,0,2,-1.6,-1.7,0,1.6,0,2,-1.6,0,2,1.6,-1.7,0,1.6,1.7,0,-1.6,1.7,0,1.6,0,2,-1.6,0,2,-1.6,1.7,0,1.6,0,2,1.6]);const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(points,3));g.computeVertexNormals();const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:0xb88e52,side:THREE.DoubleSide,roughness:.9}));m.castShadow=true;group.add(m);group.position.set(x,0,z);group.rotation.y=rotation;scene.add(group);box(2,.06,2.8,tentDark,x,.04,z);}
  tent(-5,-1,.1);tent(4,-3,-.2);tent(-5,5,.5);
  box(3,2.5,2.4,mat(0x665944),5,1.25,-1);box(1.2,2.1,.08,dark,4.8,1.05,.23);textLabel('E07',5,2.2,.29,1);
  tag(box(1.3,1.5,.05,green,5,1.2,.31),'E07');
  const fire=mesh(new THREE.ConeGeometry(.35,1.1,7),new THREE.MeshBasicMaterial({color:0xf6a24a}),0,.7,1);for(let a=0;a<Math.PI*2;a+=.6)cyl(.12,.16,.2,mat(0x746b56),Math.cos(a)*.8,.1,1+Math.sin(a)*.8);const fl=new THREE.PointLight(0xffa44b,28,10,2);fl.position.set(0,1.2,1);scene.add(fl);
  tag(box(.5,.4,.3,dark,-1.7,1.8,-2.2),'E02');for(let dx of [-.3,.3]){let leg=box(.045,1.7,.045,dark,-1.7+dx,.85,-2.2);leg.rotation.z=dx*.4}tag(cyl(.15,.15,.15,brass,-1.7,1.8,-1.99),'E02').rotation.x=Math.PI/2;
  box(2,.1,1.2,wood,1.5,.75,4);for(let x of [.8,2.2])box(.1,.75,.1,dark,x,.35,4);
  lamp(2.2,.85,4);tag(cyl(.23,.27,.4,brass,2.2,1.5,4),'E05');
  tag(box(1.1,.1,.7,green,-3,.5,2.8),'E03');packet('E06',-2,.13,2.4);
  ['E01','E04','E08','E09'].forEach((id,i)=>packet(id,-1.6+i*.85,.13,3.9));
  for(let i=0;i<7;i++)mesh(new THREE.SphereGeometry(1.3,6,4),mat(0x695c47),-11+i*3,.1,-6-Math.sin(i)*2).scale.set(1,.5,.7);
 }else{
  // Cutaway upper deck of a fictional small boat. Water and distant desert banks surround it.
  box(10,.9,15,mat(0x293e42),0,-.6,0);box(9.6,.15,14.6,wood,0,0,0);
  for(let x=-4.6;x<4.7;x+=.6)box(.02,.02,14.5,dark,x,.09,0);
  for(let x of [-4.8,4.8]){for(let z=-7;z<7;z+=1.5)cyl(.035,.035,1,brass,x,.6,z);box(.05,.06,14.5,paper,x,1.1,0)}
  box(5,3.1,.15,mat(0xd1c19b),0,1.55,-5);box(.15,3.1,4.2,mat(0xc9b98f),-2.5,1.55,-3);box(5,.2,4.3,paper,0,3.15,-3);
  tag(box(1.2,2.5,.18,green,1,1.3,-4.85),'E07');textLabel('E07',1,2.7,-4.72,.8);
  box(3.4,.18,1.8,wood,0,1.2,0);for(let x of [-1.3,1.3])for(let z of [-.5,.5])box(.1,1.2,.1,dark,x,.6,z);
  tag(box(.8,.45,.45,dark,-1,1.55,-.2),'E03');tag(cyl(.06,.06,.65,brass,-1.3,2,-.3),'E03');
  tag(box(.75,.07,.5,green,.9,1.36,.2),'E02');packet('E08',-.2,1.36,.3);packet('E05',1,1.36,-.4);
  tag(box(.9,1.1,.12,mat(0x566b64),-2.3,1.4,-2),'E06');
  lamp(2.3,.15,2.8);['E01','E04','E09'].forEach((id,i)=>packet(id,-2.3+i*.9,.15,4.4));
  for(let x of [-3.6,3.6]){let ring=mesh(new THREE.TorusGeometry(.45,.12,8,24),mat(0xcb7145),x,1,1);ring.rotation.y=Math.PI/2}
  for(let i=0;i<7;i++){let bank=mesh(new THREE.SphereGeometry(6,8,4),mat(0x625946),-30+i*11,-1,-31-Math.sin(i)*4);bank.scale.y=.5}
 }
 if(kind==='hotel')crimeScene(2.4,.03,.9,1.35);else if(kind==='hankorab')crimeScene(1.8,-.04,-.9,1.3);else crimeScene(2.9,.08,-.8,1.4);
 const glow=new THREE.Mesh(new THREE.RingGeometry(.38,.44,32),new THREE.MeshBasicMaterial({color:0xf4d38e,side:THREE.DoubleSide}));glow.rotation.x=-Math.PI/2;glow.visible=false;scene.add(glow);
 window.addEventListener('objectchosen',e=>{const o=objects.find(o=>o.userData.file===e.detail);if(o){glow.position.set(o.position.x,o.position.y+.35,o.position.z);glow.visible=true}});
 const cv=renderer.domElement;cv.setAttribute('aria-label','مشهد مكان القضية. كل الأدلة متاحة كمان بأزرار الملفات.');
 let down=null,last=null,drag=false;cv.onpointerdown=e=>{down={x:e.clientX,y:e.clientY};last=down;drag=false;cv.setPointerCapture(e.pointerId)};
 cv.onpointermove=e=>{if(!down)return;const dx=e.clientX-last.x,dy=e.clientY-last.y;if(Math.hypot(e.clientX-down.x,e.clientY-down.y)>5)drag=true;if(drag){angle-=dx*.006;elev=Math.max(.18,Math.min(.95,elev+dy*.004));cam()}last={x:e.clientX,y:e.clientY}};
 cv.onpointerup=e=>{if(down&&!drag){const r=cv.getBoundingClientRect(),p=new THREE.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),ray=new THREE.Raycaster();ray.setFromCamera(p,camera);const hit=ray.intersectObjects(objects)[0];if(hit)window.selectEvidenceFromScene(hit.object.userData.file)}down=null};cv.onpointercancel=()=>down=null;
 cv.onwheel=e=>{e.preventDefault();radius=Math.max(6,Math.min(25,radius+e.deltaY*.008));cam()};
 document.querySelector('#zin').onclick=()=>{radius=Math.max(6,radius-1);cam()};document.querySelector('#zout').onclick=()=>{radius=Math.min(25,radius+1);cam()};document.querySelector('#reset').onclick=()=>{({angle,elev,radius}=initial);cam()};
 new ResizeObserver(()=>{if(!stage.clientWidth||!stage.clientHeight)return;renderer.setSize(stage.clientWidth,stage.clientHeight);camera.aspect=stage.clientWidth/stage.clientHeight;camera.updateProjectionMatrix()}).observe(stage);
 let tick=0;renderer.setAnimationLoop(()=>{if(document.hidden||!document.body.classList.contains('view-scene')||document.body.classList.contains('interviewing'))return;if(!window.balaghReducedMotion){tick+=.008;animated.forEach((w,i)=>w.position.x+=Math.sin(tick+i)*.0008)}renderer.render(scene,camera)});
 cv.addEventListener('webglcontextlost',e=>{e.preventDefault();document.querySelector('#loading').hidden=false;document.querySelector('#loading').textContent='الرسومات وقفت. ملفات القضية كلها شغّالة من الأزرار.'});
 document.querySelector('#loading').hidden=true;window.balagh3d={scene,camera,renderer,objects,getView:()=>({angle,elev,radius}),project:id=>{const o=objects.find(x=>x.userData.file===id);if(!o)return null;const p=o.position.clone().project(camera),r=cv.getBoundingClientRect();return{x:r.left+(p.x+1)/2*r.width,y:r.top+(1-p.y)/2*r.height}}};
 }catch(e){document.querySelector('#loading').hidden=false;document.querySelector('#loading').textContent='الرسومات مش متاحة هنا، ملفات وأقوال القضية شغّالة من الأزرار.';console.error(e)}
}
window.addEventListener('caseconfig',boot);boot();

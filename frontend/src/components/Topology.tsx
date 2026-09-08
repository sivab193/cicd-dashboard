import {useEffect,useRef,useState} from 'react';
import {Github,Server,Triangle,Maximize2,Pause,Play,Network} from 'lucide-react';
import * as THREE from 'three';
import {Panel} from './ui';
export default function Topology({expanded=false}:{expanded?:boolean}){
 const mount=useRef<HTMLDivElement>(null);const [paused,setPaused]=useState(false);const [wide,setWide]=useState(expanded);const [fallback,setFallback]=useState(false);const pauseRef=useRef(false);pauseRef.current=paused;
 useEffect(()=>{const el=mount.current;if(!el)return;let renderer:THREE.WebGLRenderer;
 try{renderer=new THREE.WebGLRenderer({alpha:true,antialias:true,powerPreference:'low-power'})}catch{setFallback(true);return;}
 renderer.setPixelRatio(Math.min(devicePixelRatio,1.6));el.appendChild(renderer.domElement);
 const scene=new THREE.Scene(); const camera=new THREE.PerspectiveCamera(38,1,.1,100);camera.position.set(0,2.9,8);camera.lookAt(0,0,0);
 const group=new THREE.Group();scene.add(group);
 const sphere=new THREE.Mesh(new THREE.SphereGeometry(1.12,32,20),new THREE.MeshBasicMaterial({color:0x66ddb0,wireframe:true,transparent:true,opacity:.42}));group.add(sphere);
 const core=new THREE.Mesh(new THREE.IcosahedronGeometry(.68,1),new THREE.MeshBasicMaterial({color:0x92ffcf,wireframe:true,transparent:true,opacity:.14}));group.add(core);
 const grid=new THREE.GridHelper(24,48,0x203f39,0x132824);grid.position.y=-1.45;scene.add(grid);
 const rings:THREE.Mesh[]=[];
 [1.35,1.7,2.35].forEach((r,i)=>{const ring=new THREE.Mesh(new THREE.TorusGeometry(r,.006,8,120),new THREE.MeshBasicMaterial({color:0x6aefb3,transparent:true,opacity:.6-i*.17}));ring.rotation.x=Math.PI/2;ring.position.y=-1.2;scene.add(ring);rings.push(ring)});
 const orbit=new THREE.Mesh(new THREE.TorusGeometry(1.4,.009,8,120),new THREE.MeshBasicMaterial({color:0x8dffd0,transparent:true,opacity:.6}));orbit.rotation.set(1.1,.35,.3);group.add(orbit);
 const positions=new Float32Array(450);for(let i=0;i<450;i++)positions[i]=Math.sin(i*127.1+8.7)*7;
 const starsGeo=new THREE.BufferGeometry();starsGeo.setAttribute('position',new THREE.BufferAttribute(positions,3));const stars=new THREE.Points(starsGeo,new THREE.PointsMaterial({color:0x8fffc2,size:.017,transparent:true,opacity:.35}));scene.add(stars);
 const paths:THREE.CatmullRomCurve3[]=[];const dots:THREE.Mesh[]=[];
 [[-3,.1,0],[3,.6,-.6],[2.9,-.8,.6]].forEach(([x,y,z])=>{const path=new THREE.CatmullRomCurve3([new THREE.Vector3(0,-.1,0),new THREE.Vector3(x*.55,y+.3,z),new THREE.Vector3(x,y,z)]);paths.push(path);const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(path.getPoints(80)),new THREE.LineBasicMaterial({color:0x75edb7,transparent:true,opacity:.7}));scene.add(line);const dot=new THREE.Mesh(new THREE.SphereGeometry(.04,8,8),new THREE.MeshBasicMaterial({color:0xbeffdf}));scene.add(dot);dots.push(dot)});
 const resize=()=>{const w=el.clientWidth,h=el.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix()};const ro=new ResizeObserver(resize);ro.observe(el);resize();
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;let frame=0,t=0;let visible=true;const io=new IntersectionObserver(e=>{visible=e[0].isIntersecting});io.observe(el);
 const move=(e:PointerEvent)=>{if(reduced)return;const box=el.getBoundingClientRect();group.rotation.z=(e.clientX-box.left-box.width/2)/box.width*.12};el.addEventListener('pointermove',move);
 const loop=()=>{frame=requestAnimationFrame(loop);if(!visible||document.hidden)return;if(!reduced&&!pauseRef.current){t+=.007;sphere.rotation.y=t*.2;core.rotation.y=-t*.3;orbit.rotation.z=t*.12;dots.forEach((dot,i)=>dot.position.copy(paths[i].getPoint((t*.2+i*.3)%1)));}renderer.render(scene,camera)};loop();
 return()=>{cancelAnimationFrame(frame);ro.disconnect();io.disconnect();el.removeEventListener('pointermove',move);scene.traverse(o=>{const m=o as THREE.Mesh;if(m.geometry)m.geometry.dispose();if(m.material)(Array.isArray(m.material)?m.material:[m.material]).forEach(v=>v.dispose())});renderer.dispose();renderer.domElement.remove()};
 },[]);
 return <Panel className={`topology ${wide?'expanded':''}`} title={<><Network size={19}/>Infrastructure topology</>} subtitle="One control plane. Every connection." action={<div className="row gap"><button className="icon-button" aria-label={paused?'Play animation':'Pause animation'} onClick={()=>setPaused(!paused)}>{paused?<Play size={15}/>:<Pause size={15}/>}</button><button className="icon-button" aria-label="Expand topology" onClick={()=>setWide(!wide)}><Maximize2 size={15}/></button></div>}><div className="topology-canvas" ref={mount} aria-label="Animated infrastructure topology connecting GitHub, Vercel and OMV Server" role="img">{fallback&&<div className="fallback-orbit">◎</div>}<div className="topology-node github"><div><Github/></div><b>GitHub</b><small>Source control</small></div><div className="topology-node vercel"><div><Triangle fill="currentColor"/></div><b>Vercel</b><small>Edge deployments</small></div><div className="topology-node omv"><div><Server/></div><b>OMV Server</b><small>Self-hosted</small></div><div className="topology-center"><b>cicd.siv19.dev</b><small>CONTROL PLANE</small></div></div><div className="topology-footer"><span><i className="live-dot"/>Provider architecture</span><span>Drag your attention. Stay in control.</span></div></Panel>
}

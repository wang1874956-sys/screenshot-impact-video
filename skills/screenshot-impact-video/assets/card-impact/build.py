import pathlib,json,wave,array,math,random
p=pathlib.Path(__file__).parent
cards=[(104,214,246,216),(367,214,247,216),(631,214,247,216),(893,214,247,216),(104,454,246,219),(364,454,254,219),(631,454,247,219),(893,454,247,219)]
layers='';patches=''
for i,(x,y,w,h) in enumerate(cards):
 patches+=f'<div class="patch" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div>'
 layers+=f'<div id="card{i}" class="card crop" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background-position:-{x}px -{y}px"></div>'
words='';x=121
for i,w in enumerate([32,45,46,88]):
 words+=f'<div class="word crop" id="word{i}" style="left:{x-121}px;width:{w}px;height:37px;background-position:-{x}px -243px"></div>';x+=w
posters=''
for i in range(4):
 x,y,w,h=cards[i]
 posters+=f'<div class="poster" id="poster{i}"><div class="crop" style="width:{w}px;height:{h}px;background-position:-{x}px -{y}px"></div></div>'
labels=[('爆开 / 磁吸重组',.45),('文字 / 冲入镜头',4.05),('封面 / 高速甩入',7.45),('急停 / 回到原图',11.6)]
labelhtml=''.join(f'<div class="label" id="label{i}">{s}</div>' for i,(s,t) in enumerate(labels))
css='''
@font-face{font-family:'Microsoft YaHei';src:local('Microsoft YaHei')}
*{box-sizing:border-box}html,body{width:1600px;height:1000px;margin:0;overflow:hidden;background:#111016;color:#FFFFFF;font-family:'Microsoft YaHei',sans-serif}#root{position:relative;width:1600px;height:1000px;overflow:hidden}.header{position:absolute;left:84px;right:84px;top:26px;height:56px;display:flex;align-items:center;justify-content:space-between;z-index:100}.title{font-size:38px;font-weight:900;letter-spacing:1px}.title span{color:#FB7299}.labels{width:480px;height:48px;position:relative}.label{position:absolute;right:0;top:0;color:#FB7299;font-size:28px;font-weight:700;opacity:0;padding-top:8px}.stage{position:absolute;left:151px;top:99px;width:1180px;height:730px;transform:scale(1.1);transform-origin:top left;z-index:5}.backplane{position:absolute;inset:0}.original{position:absolute;inset:0;background:url('source.png') 0 0/1180px 730px no-repeat;border-radius:9px}.patch{position:absolute;background:#FFFFFF}.crop{background-image:url('source.png');background-size:1180px 730px;background-repeat:no-repeat}.card{position:absolute;background-color:#FFFFFF;transform-origin:center;will-change:transform}.wordstage{position:absolute;left:272px;top:400px;width:211px;height:37px;transform:scale(5);transform-origin:top left;z-index:30;opacity:0}.word{position:absolute;top:0;transform-origin:center}.posterstack{position:absolute;inset:0;z-index:40;opacity:0}.poster{position:absolute;left:485px;top:260px;width:247px;height:216px;transform:scale(2.55);transform-origin:top left;background:#FFFFFF;box-shadow:0 18px 50px #00000080;opacity:0}.slash{position:absolute;left:-200px;top:420px;width:2000px;height:150px;background:#FB7299;transform:rotate(-12deg);z-index:20;opacity:0}.flash{position:absolute;inset:0;background:#FB7299;z-index:80;opacity:0;pointer-events:none}.footer{position:absolute;left:84px;right:84px;bottom:32px;display:flex;justify-content:space-between;align-items:center;color:#BDB6C7;font-size:22px;z-index:100}.footer strong{color:#FFFFFF;font-size:25px;font-weight:500}.rail{position:absolute;left:0;bottom:0;width:1600px;height:6px;background:#FB7299;transform-origin:left;z-index:101}.ring{position:absolute;width:900px;height:900px;border:3px solid #FB7299;border-radius:50%;left:350px;top:50px;opacity:0;z-index:2}
'''
css=css.replace('transform:scale(1.1);','').replace('transform:scale(5);','')
css+='\n.header{left:0;right:0;top:0;height:92px;padding:26px 84px;background:#111016}.footer{left:0;right:0;bottom:0;height:78px;padding:0 84px 10px;background:#111016}'
css+='\n.camera{position:absolute;inset:0;transform-origin:50% 50%;perspective:1100px;transform-style:preserve-3d}.stage{perspective:900px;transform-style:preserve-3d}.card{backface-visibility:hidden}.camera>*{transform-style:preserve-3d}'
js='''
window.__timelines=window.__timelines||{};const tl=gsap.timeline({paused:true});
tl.set('.stage',{scale:1.1},0);tl.set('.wordstage',{scale:5},0);tl.set('.ring',{opacity:0,scale:1},0);
tl.from('.header',{y:-10,opacity:0,duration:.3,ease:'power3.out'},.1);
tl.from('.footer',{opacity:0,duration:.3,ease:'sine.out'},.15);
const labels=LABELS;labels.forEach((s,i)=>{if(i)tl.to('#label'+(i-1),{opacity:0,duration:.15},s[1]);tl.fromTo('#label'+i,{opacity:0,x:40},{opacity:1,x:0,duration:.2,ease:'expo.out'},s[1]+.03)});
// 1. A hard outward impulse followed by a magnetic reconstruction.
tl.to('.backplane',{opacity:.08,duration:.18},.62);
tl.fromTo('.ring',{opacity:.8,scale:.1},{opacity:0,scale:1.65,duration:.75,ease:'power3.out',immediateRender:false},.62);
const coords=CARDS;
coords.forEach((c,i)=>{const dx=[-175,-40,120,230,-200,65,145,195][i],dy=[-125,-190,-80,55,75,160,85,145][i];tl.to('#card'+i,{x:dx,y:dy,z:[70,180,-40,120,30,200,90,-50][i],rotation:[-26,17,-13,31,-19,9,25,-16][i],rotationY:[-18,22,-12,28,10,-20,16,-12][i],scale:[1.04,1.12,.92,1.05,1.1,1.05,.96,1.03][i],duration:[.26,.42,.35,.31,.48,.24,.39,.29][i],ease:['power4.out','back.out(1.7)','expo.out','power2.out'][i%4]},.62+[0,.12,.04,.18,.08,.23,.15,.02][i]);tl.to('#card'+i,{x:dx+[28,-35,20,-18,30,-24,17,-10][i],y:dy+[14,-20,32,-16,-25,18,-30,12][i],rotation:[-20,23,-19,25,-24,14,19,-21][i],duration:[.65,.9,.8,.72,.9,.6,.8,.75][i],ease:'sine.inOut'},1.22);tl.to('#card'+i,{x:0,y:0,z:0,rotation:0,rotationY:0,scale:1,duration:.68,ease:'elastic.out(1,.4)'},[2.31,2.45,2.2,2.57,2.39,2.23,2.5,2.29][i]);});
tl.to('.backplane',{opacity:1,duration:.35},3.15);
tl.to('.stage',{x:-10,duration:.04},.66);tl.to('.stage',{x:12,duration:.04},.71);tl.to('.stage',{x:-5,duration:.04},.77);tl.to('.stage',{x:0,duration:.09},.83);
// 2. The actual raster title is split into four fragments and slammed on screen.
tl.to('.stage',{opacity:.12,scale:1.02,duration:.22,ease:'power2.in'},4.05);
tl.to('.wordstage',{opacity:1,duration:.08},4.15);
for(let i=0;i<4;i++)tl.from('#word'+i,{y:i%2?95:-95,x:(i-1.5)*30,rotation:i%2?-20:20,opacity:0,duration:.25,ease:'expo.out',immediateRender:false},4.18+i*.1);
tl.to('.wordstage',{scale:5.4,x:-42,y:-7,duration:.1,ease:'power4.out'},4.72);
tl.to('.wordstage',{scale:5,x:0,y:0,duration:.6,ease:'elastic.out(1,.4)'},4.83);
tl.to('.stage',{x:-14,duration:.035},4.73);tl.to('.stage',{x:11,duration:.035},4.78);tl.to('.stage',{x:0,duration:.1},4.83);
tl.to('.wordstage',{rotation:-2,y:-13,duration:.25,ease:'power3.out'},5.75);tl.to('.wordstage',{rotation:0,y:0,duration:.45,ease:'elastic.out(1,.4)'},6.01);
tl.to('.wordstage',{opacity:0,scale:6.5,duration:.22,ease:'power3.in'},7.35);
tl.fromTo('.slash',{opacity:1,x:-2100},{opacity:1,x:2100,duration:.45,ease:'expo.inOut'},7.32);tl.set('.slash',{opacity:0},7.78);
// 3. Different images arrive from different directions, with a forceful stop.
tl.to('.stage',{opacity:0,duration:.2},7.4);tl.to('.posterstack',{opacity:1,duration:.12},7.5);
const ps=[{x:-30,y:-25,rotation:-7,fromX:-1500,fromY:-180,fromR:-45},{x:45,y:0,rotation:8,fromX:1600,fromY:-160,fromR:45},{x:5,y:40,rotation:-4,fromX:30,fromY:1200,fromR:-30},{x:-15,y:20,rotation:3,fromX:1600,fromY:400,fromR:65}];
ps.forEach((v,i)=>{const t=7.65+i*.7;tl.fromTo('#poster'+i,{opacity:1,x:v.fromX,y:v.fromY,rotation:v.fromR,scale:3.1},{opacity:1,x:v.x,y:v.y,rotation:v.rotation,scale:2.55,duration:.32,ease:'expo.out'},t);tl.to('#poster'+i,{rotation:v.rotation+(i%2?-2:2),duration:.34,ease:'elastic.out(1,.45)'},t+.33);});
// 4. The stack contracts as the original layout snaps back together.
tl.to('.posterstack',{opacity:0,scale:.2,rotation:18,duration:.32,ease:'power4.in'},11.5);
tl.to('.stage',{opacity:1,scale:1.1,duration:.18},11.65);
tl.set('.backplane',{opacity:0},11.64);
coords.forEach((c,i)=>{tl.fromTo('#card'+i,{x:i%2?850:-850,y:i<4?-140:180,rotation:i%2?35:-35,scale:.55},{x:0,y:0,rotation:0,scale:1,duration:.62,ease:'back.out(1.25)'},11.7+i*.045)});
tl.fromTo('.ring',{opacity:.7,scale:1.6},{opacity:0,scale:.1,duration:.75,ease:'power2.in',immediateRender:false},11.7);
tl.to('.backplane',{opacity:1,duration:.45,ease:'power2.out'},12.5);
// One local finishing accent, then an unambiguous still original.
tl.set('#card1',{zIndex:10},13.4);tl.to('#card1',{y:-24,scale:1.1,rotation:-2,duration:.16,ease:'power4.out'},13.45);tl.to('#card1',{y:0,scale:1,rotation:0,duration:.7,ease:'elastic.out(1,.4)'},13.63);tl.set('#card1',{zIndex:0},14.5);
tl.to('.stage',{scale:1.11,x:-6,y:-4,duration:.15,ease:'power2.out'},14.7);tl.to('.stage',{scale:1.1,x:0,y:0,duration:.4,ease:'power3.out'},14.86);
// An authored virtual camera: punch in, oblique sweep, pull back, and settle.
tl.to('.camera',{scale:1.12,x:30,y:-25,rotation:-3,duration:.3,ease:'power4.out'},.6);
tl.to('.camera',{x:-55,y:20,rotation:2.5,scale:1.16,duration:.75,ease:'power2.inOut'},1.35);
tl.to('.camera',{scale:1,x:0,y:0,rotation:0,duration:.8,ease:'power3.inOut'},2.35);
tl.to('.camera',{scale:1.14,x:-35,y:-20,rotation:-4,duration:.24,ease:'expo.out'},4.22);
tl.to('.camera',{scale:1.06,x:45,y:10,rotation:2,duration:.6,ease:'power3.inOut'},5.15);
tl.to('.camera',{x:-40,y:-10,rotation:-1,scale:1.1,duration:.3,ease:'power4.out'},6.1);
tl.to('.camera',{scale:1,x:0,y:0,rotation:0,duration:.32,ease:'power2.inOut'},7.3);
tl.to('.camera',{rotation:-6,x:45,y:-10,scale:1.08,duration:.25,ease:'power4.out'},7.67);
tl.to('.camera',{rotation:4,x:-35,y:25,scale:1.12,duration:.32,ease:'power3.inOut'},8.39);
tl.to('.camera',{rotation:-3,x:15,y:-35,scale:1.03,duration:.3,ease:'expo.out'},9.09);
tl.to('.camera',{rotation:1,x:-20,y:0,scale:1.12,duration:.28,ease:'power4.out'},9.8);
tl.to('.camera',{rotation:-8,scale:.82,x:40,y:20,duration:.3,ease:'power4.in'},11.5);
tl.to('.camera',{rotation:0,scale:1,x:0,y:0,duration:.6,ease:'back.out(1.1)'},11.83);
tl.to('.camera',{scale:1.05,x:5,y:5,duration:.16,ease:'power3.out'},13.46);
tl.to('.camera',{scale:1,x:0,y:0,duration:.6,ease:'power2.inOut'},13.65);
tl.from('.rail',{scaleX:0,duration:18,ease:'none'},0);
window.__timelines.main=tl;
'''.replace('LABELS',json.dumps(labels,ensure_ascii=False)).replace('CARDS',json.dumps(cards))
doc=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><script src="gsap.min.js"></script><style>{css}</style></head><body><div id="root" data-composition-id="main" data-start="0" data-duration="18" data-width="1600" data-height="1000"><div class="ring" data-layout-ignore></div><div class="stage" data-layout-allow-overflow><div class="backplane"><div class="original"></div>{patches}</div>{layers}</div><div class="wordstage" data-layout-allow-overflow>{words}</div><div class="posterstack" data-layout-allow-overflow>{posters}</div><div class="slash" data-layout-ignore></div><div class="header"><div class="title">截图 <span>×</span> 冲击动效</div><div class="labels">{labelhtml}</div></div><div class="footer"><strong>爆开 · 冲屏 · 甩入 · 急停</strong><span>动效样例 / 手工分层</span></div><div class="rail" data-layout-ignore></div><audio id="fx" data-start="0" data-duration="18" data-track-index="2" src="impact.wav" data-volume=".7"></audio></div><script>{js}</script></body></html>'''
doc=doc.replace('<div class="ring" data-layout-ignore>', '<div class="camera" data-layout-allow-overflow><div class="ring" data-layout-ignore>',1).replace('<div class="header">','</div><div class="header">',1)
doc=doc.replace('爆开 · 冲屏 · 甩入 · 急停','不规则轨迹 · 变速 · 镜头推拉与倾斜')
(p/'index.html').write_text(doc,'utf-8')
rate=48000;buf=array.array('f',[0])*(18*rate);rng=random.Random(19)
events=[(.62,1),(2.2,.65),(4.18,.55),(4.48,.55),(4.72,1),(5.75,.55),(7.65,.85),(8.35,.85),(9.05,.85),(9.75,1),(11.7,1),(13.45,.7),(14.7,.45)]
for t,strength in events:
 # Original synth whoosh leading into a soft-limited low-frequency impact.
 for j in range(int(rate*.18)):
  u=j/rate;at=int((t-.18)*rate)+j
  if at>=0:buf[at]+=.13*strength*(u/.18)**2*(rng.random()*2-1)
 for j in range(int(rate*.42)):
  u=j/rate;env=math.exp(-u*12)*(1-math.exp(-u*600));phase=2*math.pi*(65*u+55*(1-math.exp(-u*22))/22)
  buf[int(t*rate)+j]+=strength*env*(.5*math.sin(phase)+.08*(rng.random()*2-1)*math.exp(-u*40))
pcm=array.array('h',(round(max(-.95,min(.95,x))*32767) for x in buf))
with wave.open(str(p/'impact.wav'),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(pcm.tobytes())
print('18-second high-impact variant built.')

import pathlib,json,math,random,wave,array
p=pathlib.Path(__file__).parent
rects=[]
for row in range(3):
 for col in range(7):rects.append([1200+col*60,155+row*79,60,76])
for col in range(2):rects.append([1200+col*60,392,60,76])
for col in range(4):rects.append([720+col*60,155,60,76])
sprites='';patches=''
for i,(x,y,w,h) in enumerate(rects):
 sprites+=f'<div class="icon" id="i{i}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background-position:-{x}px -{y}px"></div>'
 patches+=f'<div class="patch" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background-position:-1740px -{y}px"></div>'
hero=''
for j,i in enumerate([5,9,2]):
 x,y,w,h=rects[i];hero+=f'<div class="hero" id="h{j}" style="background-position:-{x}px -{y}px"></div>'
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><script src="gsap.min.js"></script><style>
@font-face{font-family:YaHei;src:local('Microsoft YaHei')}
*{box-sizing:border-box}html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:#09090d;color:white;font-family:YaHei,sans-serif}
#root{position:relative;width:1920px;height:1080px;overflow:hidden}.viewport{position:absolute;width:2048px;height:1152px;transform:scale(.9375);transform-origin:top left}.camera{position:absolute;inset:0;transform-origin:0 0;perspective:1300px;transform-style:preserve-3d}.desktop{position:absolute;inset:0;background:url(source.png) 0 0/2048px 1152px no-repeat}.patches{position:absolute;inset:0;opacity:0}.patch{position:absolute;background-image:url(source.png);background-size:2048px 1152px}.icons{position:absolute;inset:0;perspective:1400px;transform-style:preserve-3d}.icon,.hero{position:absolute;background-image:url(source.png);background-size:2048px 1152px;transform-origin:center;backface-visibility:hidden;will-change:transform}.hero{left:994px;top:465px;width:60px;height:76px;opacity:0;z-index:50}.heroes{position:absolute;inset:0;perspective:1400px;transform-style:preserve-3d}.halo{position:absolute;left:575px;top:115px;width:900px;height:900px;border:2px solid #edc779;border-radius:50%;opacity:0;transform:rotateX(60deg);pointer-events:none}.beam{position:absolute;left:0;top:560px;width:2048px;height:3px;background:#edc779;opacity:0;transform-origin:center}.bars{position:absolute;inset:0;pointer-events:none;z-index:100}.top{position:absolute;top:0;left:0;right:0;height:86px;background:#09090d;display:flex;align-items:center;justify-content:space-between;padding:0 60px}.brand{font-size:27px;letter-spacing:4px;color:#edc779}.chapter{font-size:27px;font-weight:600}.bottom{position:absolute;bottom:0;left:0;right:0;height:55px;background:#09090d;display:flex;align-items:center;justify-content:space-between;padding:0 60px;font-size:18px;color:#cabf9f}.progress{position:absolute;bottom:0;left:0;width:1920px;height:3px;background:#edc779;transform-origin:left}
</style></head><body><div id="root" data-composition-id="main" data-start="0" data-duration="20" data-width="1920" data-height="1080"><div class="viewport" data-layout-allow-overflow><div class="camera" data-layout-allow-overflow><div class="desktop"><div class="patches">PATCHES</div></div><div class="halo" data-layout-ignore></div><div class="icons" data-layout-allow-overflow>SPRITES</div><div class="beam" data-layout-ignore></div></div><div class="heroes" data-layout-allow-overflow>HERO</div></div><div class="bars"><div class="top"><div class="brand">DESKTOP / ZERO GRAVITY</div><div class="chapter">01 / 俯冲 · 脱离桌面</div></div><div class="bottom"><span>不规则轨迹 / 空间环绕 / 镜头穿行</span><span>动效样片 · 手工分层</span></div></div><div class="progress" data-layout-ignore></div><audio src="impact.wav" data-start="0" data-duration="20" data-track-index="2" data-volume=".8"></audio></div><script>
const rects=RECTS;window.__timelines={};const tl=gsap.timeline({paused:true});window.__timelines.main=tl;
tl.set('.bars',{opacity:0},0);tl.to('.bars',{opacity:1,duration:.3},.3);
tl.to('.camera',{scale:1.95,x:-1690,y:35,rotation:-3,duration:.65,ease:'expo.inOut'},.8);
tl.to('.patches',{opacity:1,duration:.05},1.42);
rects.forEach((r,i)=>{tl.to('#i'+i,{y:-10-(i%4)*6,rotation:(i%2?1:-1)*(8+i%5),scale:1.1+(i%3)*.12,duration:.2,ease:'power3.out'},1.47+(i%7)*.025)});
tl.to('.camera',{scale:1.04,x:-30,y:-15,rotation:0,duration:.8,ease:'expo.inOut'},1.95);
tl.to('.desktop',{opacity:.19,duration:.55},2.05);
const positions=[];
rects.forEach((r,i)=>{
 const c=i%7,row=Math.floor(i/7),px=270+c*242+Math.sin(i*3.1)*63,py=235+row*211+Math.cos(i*2.3)*56;
 positions.push([px,py]);
 tl.to('#i'+i,{x:px-r[0],y:py-r[1],z:(i%5-2)*75,scale:1.8+(i%4)*.43,rotation:(i%2?1:-1)*(7+i%13),rotationY:(i%3-1)*22,duration:.55+(i%4)*.09,ease:['expo.out','back.out(1.5)','power4.out'][i%3]},2.18+((i*7)%13)*.032);
 tl.to('#i'+i,{x:px-r[0]+Math.sin(i)*35,y:py-r[1]+Math.cos(i*2)*22,rotation:(i%2?1:-1)*5,duration:1.1,ease:'sine.inOut'},3.22+(i%4)*.03);
});
tl.to('.camera',{scale:1.14,x:-110,y:-65,rotation:2,duration:1.1,ease:'power2.inOut'},3.4);
tl.set('.chapter',{textContent:'02 / 引力旋涡 · 加速环绕'},4.75);
tl.to('.halo',{opacity:.6,scale:1.4,rotationZ:-20,duration:.4,ease:'power3.out'},4.8);
rects.forEach((r,i)=>{
 let a=i/rects.length*Math.PI*2;
 for(let k=0;k<4;k++){
  let ang=a+k*.91,rx=560+(i%3)*80,ry=260+(i%4)*25;
  tl.to('#i'+i,{x:1024+Math.cos(ang)*rx-r[0]-30,y:556+Math.sin(ang)*ry-r[1]-38,z:Math.sin(ang)*230,scale:1.8+(1+Math.sin(ang))*.65,rotation:Math.sin(ang)*28,rotationY:Math.cos(ang)*22,duration:k===0?.65:.58,ease:k===0?'expo.inOut':'none'},4.85+k*.6+(k===0?(i%5)*.025:0));
 }
});
tl.to('.camera',{scale:.95,x:30,y:15,rotation:-5,duration:.6,ease:'power3.inOut'},4.85);
tl.to('.camera',{scale:1.18,x:-155,y:-20,rotation:4,duration:1.45,ease:'power2.inOut'},5.55);
tl.to('.halo',{rotationZ:100,scale:1.05,duration:2.1,ease:'power2.in'},5.2);
tl.set('.chapter',{textContent:'03 / 穿越图标 · 冲入镜头'},7.6);
rects.forEach((r,i)=>{const a=i/27*Math.PI*2;tl.to('#i'+i,{x:1024+Math.cos(a)*1600-r[0],y:576+Math.sin(a)*1000-r[1],z:400,rotation:(i%2?1:-1)*100,opacity:.1,scale:4,duration:.46+(i%3)*.06,ease:'expo.in'},7.65+(i%4)*.025)});
tl.to('.halo',{opacity:0,scale:2.3,duration:.5},7.65);tl.to('.desktop',{opacity:.11,duration:.3},7.7);
const heroTimes=[8.05,9.8,11.55];
heroTimes.forEach((t,i)=>{
 tl.fromTo('#h'+i,{opacity:1,x:i%2?1200:-1200,y:i===1?-600:300,scale:11,rotation:i%2?40:-40,rotationY:i%2?-35:35},{opacity:1,x:0,y:0,scale:6.6,rotation:i===1?7:-7,rotationY:0,duration:.36,ease:'expo.out'},t);
 tl.to('#h'+i,{scale:7.05,rotation:i===1?2:-2,x:i%2?-30:30,duration:.65,ease:'sine.inOut'},t+.4);
 tl.to('#h'+i,{opacity:0,x:i%2?-1800:1800,y:-180,scale:10,rotation:i%2?-45:45,duration:.34,ease:'expo.in'},t+1.3);
 tl.fromTo('.beam',{opacity:.8,scaleX:0,rotation:i%2?16:-16},{opacity:0,scaleX:1.4,duration:.55,ease:'expo.out',immediateRender:false},t);
});
tl.set('.chapter',{textContent:'04 / 散射 · 精准归位'},13.35);
tl.to('.camera',{scale:1,x:0,y:0,rotation:0,duration:.1},13.35);
rects.forEach((r,i)=>{
 const a=i/27*Math.PI*2;
 tl.fromTo('#i'+i,{opacity:1,x:1024+Math.cos(a)*1400-r[0],y:570+Math.sin(a)*1000-r[1],z:100,rotation:(i%2?1:-1)*120,rotationY:0,scale:4},{opacity:1,x:positions[i][0]-r[0],y:positions[i][1]-r[1],z:(i%4-1)*60,rotation:(i%2?1:-1)*12,scale:2.2,duration:.65,ease:'expo.out'},13.45+((i*3)%11)*.025);
 tl.to('#i'+i,{x:0,y:0,z:0,scale:1,rotation:0,rotationY:0,duration:.75,ease:'back.out(1.2)'},15.2+((i*7)%17)*.035);
});
tl.to('.camera',{scale:.9,x:110,y:40,rotation:-3,duration:.35,ease:'power3.out'},13.5);
tl.to('.camera',{scale:1.08,x:-90,y:-30,rotation:2,duration:.55,ease:'power2.inOut'},14.3);
tl.to('.camera',{scale:1,x:0,y:0,rotation:0,duration:.8,ease:'power3.inOut'},15.15);
tl.to('.desktop',{opacity:1,duration:.8},15.6);tl.set('.patches',{opacity:0},16.7);
tl.set('.chapter',{textContent:'一张截图 / 另一种运动方式'},17);
tl.to('.bars',{opacity:0,duration:.5},18.3);tl.from('.progress',{scaleX:0,duration:20,ease:'none'},0);
</script></body></html>'''
html=html.replace('PATCHES',patches).replace('SPRITES',sprites).replace('HERO',hero).replace('RECTS',json.dumps(rects))
html=html.replace('<audio src=', '<audio id="impact-audio" src=').replace('.bars{position:', '.bars{opacity:0;position:').replace("tl.set('.bars',{opacity:0},0);",'')
html=html.replace('transform-style:preserve-3d;','')
html=html.replace("duration:.36,ease:'expo.out'},t)","duration:.36,ease:'expo.out',immediateRender:false},t)")
html=html.replace("duration:.65,ease:'expo.out'},13.45", "duration:.65,ease:'expo.out',immediateRender:false},13.45")
(p/'index.html').write_text(html,'utf-8')
rate=48000;buf=array.array('f',[0])*(20*rate);rng=random.Random(93)
events=[(.95,.6),(1.48,.4),(2.28,1),(4.95,.8),(5.55,.3),(6.15,.4),(6.75,.5),(7.75,.9),(8.08,1),(9.83,1),(11.58,1),(13.5,.9),(15.35,.7),(16.5,.4)]
for t,s in events:
 for j in range(int(.28*rate)):
  u=j/rate;idx=int((t-.28)*rate)+j
  if idx>=0:buf[idx]+=.08*s*(u/.28)**2*(rng.random()*2-1)
 for j in range(int(.55*rate)):
  u=j/rate;env=math.exp(-u*10)*(1-math.exp(-u*500));phase=2*math.pi*(47*u+70*(1-math.exp(-u*18))/18)
  buf[int(t*rate)+j]+=s*env*(.55*math.sin(phase)+.05*(rng.random()*2-1)*math.exp(-u*30))
pcm=array.array('h',(round(max(-.92,min(.92,v))*32767) for v in buf))
with wave.open(str(p/'impact.wav'),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(pcm.tobytes())
print('Built 20s / 27 icon layers / 3 hero passes.')

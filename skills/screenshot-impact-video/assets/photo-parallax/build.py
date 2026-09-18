"""Build a configurable 2.5D photo composition from motion-plan.json (stdlib only)."""
import array
import html
import json
import math
from pathlib import Path
import random
import re
import struct
import wave


def number(value, lo, hi, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not lo <= value <= hi:
        raise ValueError(f'{name} must be a finite number in [{lo}, {hi}]')
    return value


def camera_pose(width, height, scale, rotation, focus):
    """Constrain rotated photo edges to cover its viewport at a sampled pose."""
    a = math.radians(rotation)
    c, s = math.cos(a), math.sin(a)
    rx = (abs(c) * width + abs(s) * height) / 2
    ry = (abs(s) * width + abs(c) * height) / 2
    scale = max(scale, rx * 2 / width, ry * 2 / height)
    if rotation:
        scale *= 1.025
    bx, by = scale * width / 2 - rx, scale * height / 2 - ry
    tx = min(bx, max(-bx, -scale * (focus[0] - .5) * width))
    ty = min(by, max(-by, -scale * (focus[1] - .5) * height))
    return {'x': c * tx - s * ty, 'y': s * tx + c * ty, 'scale': scale, 'rotation': rotation}


def local_asset(root, name):
    if not isinstance(name, str) or Path(name).is_absolute():
        raise ValueError('Asset must be a relative project file')
    target = (root / name).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        raise ValueError(f'Missing or out-of-project asset: {name}')
    return html.escape(name.replace('\\', '/'), quote=True)


def alpha_png(root, name, expected_size):
    """Require a source-sized matte or a rect-sized transparent cutout."""
    asset = local_asset(root, name)
    path = (root / name).resolve()
    with path.open('rb') as stream:
        header = stream.read(26)
    if len(header) < 26 or header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR':
        raise ValueError(f'{name} must be a PNG with an alpha channel')
    width, height = struct.unpack('>II', header[16:24])
    if (width, height) != expected_size or header[25] not in (4, 6):
        raise ValueError(f'{name} must be an alpha PNG of size {expected_size[0]}x{expected_size[1]}')
    return asset


def bounds(rect, width, height):
    if not isinstance(rect, list) or len(rect) != 4:
        raise ValueError('rect must be [x,y,width,height]')
    x, y, w, h = [number(v, 0, 32768, 'rect coordinate') for v in rect]
    if w <= 0 or h <= 0 or x + w > width or y + h > height:
        raise ValueError('rect must stay inside source dimensions')
    return x, y, w, h


def synth_audio(path, duration, seed, events):
    rate = 48000
    buf = array.array('f', [0]) * round(duration * rate)
    rng = random.Random(seed)
    for t in events:
        for j in range(round(.2 * rate)):
            at = round((t - .2) * rate) + j
            if 0 <= at < len(buf):
                buf[at] += .08 * (j / (.2 * rate)) ** 2 * rng.uniform(-1, 1)
        for j in range(round(.48 * rate)):
            at = round(t * rate) + j
            if at >= len(buf):
                break
            u = j / rate
            buf[at] += .48 * math.exp(-u * 12) * (1 - math.exp(-u * 500)) * math.sin(2 * math.pi * (48 * u + 3 * (1 - math.exp(-u * 18))))
    pcm = array.array('h', (round(max(-.9, min(.9, x)) * 32767) for x in buf))
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(pcm.tobytes())


def build(root):
    root = Path(root)
    plan = json.loads((root / 'motion-plan.json').read_text(encoding='utf-8'))
    src, out, style = plan['source'], plan['output'], plan['style']
    if src.get('orientation', 1) != 1:
        raise ValueError('Normalize EXIF orientation before assigning photo layer coordinates.')
    sw, sh = [number(src[k], 1, 32768, k) for k in ('width', 'height')]
    ow, oh = [number(out[k], 2, 4096, k) for k in ('width', 'height')]
    if any(int(v) != v or v % 2 for v in (ow, oh)):
        raise ValueError('Output dimensions must be even integers')
    duration = number(out['duration'], 2, 60, 'duration')
    fps = number(out['fps'], 1, 60, 'fps')
    if int(fps) != fps:
        raise ValueError('fps must be an integer')
    intensity = style.get('intensity', 'strong')
    mode = style.get('camera', 'dynamic')
    if intensity not in ('subtle', 'balanced', 'strong') or mode not in ('static', 'cinematic', 'dynamic'):
        raise ValueError('Unknown intensity or camera mode')
    sound = style.get('sound', True)
    if not isinstance(sound, bool):
        raise ValueError('sound must be boolean')
    seed = int(number(style.get('seed', 19), 0, 2147483647, 'seed'))
    gain = {'subtle': .35, 'balanced': .65, 'strong': 1}[intensity]
    filename = local_asset(root, src['file'])
    fit = min(ow / sw, oh / sh)
    left, top = (ow - sw * fit) / 2, (oh - sh * fit) / 2
    nodes = []
    review = []
    js = ["window.__timelines={};const tl=gsap.timeline({paused:true});window.__timelines.main=tl;"]
    layers = plan.get('layers', [])
    if len(layers) > 80:
        raise ValueError('At most 80 layers per composition')
    ids = set()
    focus = [.5, .6]
    for i, item in enumerate(layers):
        lid = item.get('id', f'layer-{i}')
        if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_-]*', lid) or lid in ids:
            raise ValueError('Each layer needs a unique simple id')
        ids.add(lid)
        x, y, w, h = bounds(item['rect'], sw, sh)
        clip = ''
        if 'cutout' in item and 'polygon' in item:
            raise ValueError('Use either an alpha cutout or a polygon for one layer')
        if 'polygon' in item:
            points = item['polygon']
            if not 3 <= len(points) <= 100:
                raise ValueError('polygon needs 3–100 points')
            coords = []
            for pair in points:
                if len(pair) != 2:
                    raise ValueError('polygon points need x and y')
                px, py = number(pair[0], x, x+w, 'polygon x'), number(pair[1], y, y+h, 'polygon y')
                coords.append(f'{px-x}px {py-y}px')
            clip = 'clip-path:polygon(' + ','.join(coords) + ');'
        if 'cutout' in item:
            if any(int(v) != v for v in (w, h)):
                raise ValueError('Alpha cutout rect needs integer width and height')
            cutout = alpha_png(root, item['cutout'], (int(w), int(h)))
            content = f'<img src="{cutout}" style="width:{w}px;height:{h}px">'
        else:
            review.append(f'{lid}: inspect hard polygon/rectangle edges at maximum displacement')
            content = f'<img src="{filename}" style="left:-{x}px;top:-{y}px;width:{sw}px;height:{sh}px">'
        nodes.append(f'<div id="{lid}" class="cut" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;{clip}">{content}</div>')
        start = number(item.get('start', duration*.18+i*.06), 0, duration*.72, 'layer start')
        length = number(item.get('move_duration', duration*.07), .05, duration*.25, 'move duration')
        if start + length > duration * .79:
            raise ValueError('Layer entrance overlaps return segment')
        dx = number(item.get('dx', (i%2*2-1)*sw*.06), -sw, sw, 'dx') * gain
        dy = number(item.get('dy', -sh*.10), -sh, sh, 'dy') * gain
        rot = number(item.get('rotation', (i%2*2-1)*12), -90, 90, 'rotation') * gain
        scale = number(item.get('scale', 1.1), .2, 4, 'layer scale')
        target = {'x': dx, 'y': dy, 'rotation': rot, 'scale': 1+(scale-1)*gain, 'duration': length, 'ease': 'back.out(1.15)'}
        js.append(f"tl.to('#{lid}',{json.dumps(target)},{start});")
        drift = min(duration*.14, duration*.79-start-length)
        if drift > .01:
            js.append(f"tl.to('#{lid}',{{x:{dx*.82},y:{dy*1.10},rotation:{rot*.6},duration:{drift},ease:'sine.inOut'}},{start+length});")
        js.append(f"tl.to('#{lid}',{{x:0,y:0,rotation:0,scale:1,duration:{duration*.09},ease:'power3.inOut'}},{duration*.79});")
        if i == 0:
            focus = [(x+w/2)/sw, (y+h/2)/sh]
    patches = []
    if layers and not plan.get('patches'):
        review.append('Moving layers have no clean background patches; inspect original-position ghosts')
    for i, patch in enumerate(plan.get('patches', [])):
        x, y, w, h = bounds(patch['rect'], sw, sh)
        asset = local_asset(root, patch['file'])
        mask_css = ''
        if 'mask' in patch:
            mask = alpha_png(root, patch['mask'], (int(sw), int(sh)))
            mask_css = (f'-webkit-mask-image:url(&quot;{mask}&quot;);mask-image:url(&quot;{mask}&quot;);'
                        f'-webkit-mask-size:{sw}px {sh}px;mask-size:{sw}px {sh}px;'
                        f'-webkit-mask-position:-{x}px -{y}px;mask-position:-{x}px -{y}px;')
        else:
            review.append(f'patch-{i}: no alpha mask; inspect hard rectangular edges')
        patches.append(f'<div class="patch" id="patch-{i}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;{mask_css}"><img src="{asset}" style="left:-{x}px;top:-{y}px;width:{sw}px;height:{sh}px"></div>')
        start = number(patch.get('start', duration*.17), 0, duration*.72, 'patch start')
        js.append(f"tl.to('#patch-{i}',{{opacity:1,duration:.08}},{start});tl.to('#patch-{i}',{{opacity:0,duration:.12}},{duration*.885});")
    lights = []
    for i, item in enumerate(plan.get('lights', [])):
        x,y,w,h = bounds(item['rect'],sw,sh)
        color = item.get('color','#bd5dff')
        if not isinstance(color,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',color):
            raise ValueError('Light color must be #RRGGBB')
        opacity = number(item.get('opacity',.4),0,1,'light opacity')*gain
        start = number(item.get('start',duration*.3),0,duration*.72,'light start')
        length = number(item.get('duration',duration*.18),.1,duration*.3,'light duration')
        if start+length > duration*.91:
            raise ValueError('Light should finish before the final hold')
        lights.append(f'<div class="light" id="light-{i}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:radial-gradient(ellipse,{color},transparent 70%)"></div>')
        js.append(f"tl.to('#light-{i}',{{opacity:{opacity},duration:{length*.2}}},{start});tl.to('#light-{i}',{{opacity:0,duration:{length*.8}}},{start+length*.2});")
    if 'focus' in style:
        if not isinstance(style['focus'],list) or len(style['focus']) != 2:
            raise ValueError('focus must be [x,y] fractions')
        focus = [number(v,0,1,'focus') for v in style['focus']]
    if mode != 'static':
        turn = 0 if mode == 'cinematic' else 4 * gain
        for at, length, zoom, angle, focal in [(.06,.10,1+.32*gain,-turn,focus),(.28,.16,1+.43*gain,turn,[min(.8,focus[0]+.08),focus[1]]),(.53,.10,1+.22*gain,-turn*.5,[.5,.52]),(.76,.15,1,0,[.5,.5])]:
            pose = camera_pose(sw, sh, zoom, angle, focal)
            pose.update(duration=duration*length, ease='power3.inOut')
            js.append(f"tl.to('.camera',{json.dumps(pose)},{duration*at});")
    audio = '<audio id="motion-audio" src="impact.wav" data-start="0" data-duration="'+str(duration)+'" data-track-index="2" data-volume=".7"></audio>' if sound else ''
    doc = f'''<!doctype html><html><head><meta charset="utf-8"><script src="gsap.min.js"></script><style>
*{{box-sizing:border-box}}html,body{{margin:0;width:{ow}px;height:{oh}px;overflow:hidden;background:#131116}}#root{{position:relative;width:{ow}px;height:{oh}px;overflow:hidden}}.stage{{position:absolute;left:{left}px;top:{top}px;width:{sw}px;height:{sh}px;transform:scale({fit});transform-origin:0 0;overflow:hidden}}.camera{{position:absolute;inset:0;transform-origin:center}}.base{{position:absolute;width:100%;height:100%;inset:0}}.cut,.patch{{position:absolute;overflow:hidden}}.cut img,.patch img{{position:absolute;max-width:none}}.patch{{opacity:0}}
</style></head><body><div id="root" data-composition-id="main" data-start="0" data-duration="{duration}" data-width="{ow}" data-height="{oh}"><div class="stage" data-layout-allow-overflow><div class="camera" data-layout-allow-overflow><img class="base" src="{filename}">{''.join(patches)}{''.join(nodes)}</div></div>{audio}</div><script>{''.join(js)}</script></body></html>'''
    doc=doc.replace('</style>', '.light{position:absolute;opacity:0;mix-blend-mode:screen;pointer-events:none}</style>')
    doc=doc.replace(''.join(patches)+''.join(nodes), ''.join(patches)+''.join(lights)+''.join(nodes),1) if (patches or nodes) else doc.replace(f'<img class="base" src="{filename}">',f'<img class="base" src="{filename}">'+''.join(lights),1)
    (root/'index.html').write_text(doc, encoding='utf-8')
    (root/'quality-review.json').write_text(json.dumps({'manual_review_required': bool(layers or patches),
        'checks': review, 'note': 'File checks cannot certify a natural-looking composite.'},
        ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    if sound:
        synth_audio(root/'impact.wav', duration, seed, [duration*f for f in (.14,.25,.46,.61,.81)])
    package = root/'package.json'
    if package.is_file():
        data = json.loads(package.read_text(encoding='utf-8'))
        data['scripts']['render'] = f'hyperframes render --output demo.mp4 --fps {fps} --quality high'
        package.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
    print(f'Built {duration}s photo composition: {len(layers)} layers, camera={mode}, intensity={intensity}, sound={sound}')
    for item in review:
        print(f'REVIEW: {item}')


if __name__ == '__main__':
    build(Path(__file__).resolve().parent)

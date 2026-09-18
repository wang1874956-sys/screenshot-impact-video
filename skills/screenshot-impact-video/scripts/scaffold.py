"""Create an editable screenshot animation project; never guesses element regions."""
import argparse
import json
from pathlib import Path
import shutil
import struct


def image_info(source):
    with source.open('rb') as stream:
        header = stream.read(24)
    if len(header) == 24 and header[:8] == b'\x89PNG\r\n\x1a\n' and header[12:16] == b'IHDR':
        width, height = struct.unpack('>II', header[16:24])
        extension, orientation = '.png', 1
    elif header[:2] == b'\xff\xd8':
        width, height, orientation = jpeg_info(source)
        extension = '.jpg'
    else:
        raise ValueError('This helper accepts PNG and JPEG. Export other formats before creating a project.')
    if not (0 < width <= 32768 and 0 < height <= 32768):
        raise ValueError('Invalid or unsupported image dimensions.')
    return width, height, extension, orientation


def jpeg_info(source):
    width = height = 0
    orientation = 1
    with source.open('rb') as stream:
        stream.read(2)
        while True:
            start = stream.read(1)
            if not start:
                break
            if start != b'\xff':
                raise ValueError('Invalid JPEG marker')
            marker = stream.read(1)
            while marker == b'\xff':
                marker = stream.read(1)
            if not marker or marker[0] in (0xda, 0xd9):
                break
            if marker[0] in (0x01, *range(0xd0, 0xd9)):
                continue
            size_bytes = stream.read(2)
            if len(size_bytes) != 2:
                raise ValueError('Truncated JPEG')
            size = struct.unpack('>H', size_bytes)[0]
            if size < 2:
                raise ValueError('Invalid JPEG segment length')
            body = stream.read(size-2)
            if len(body) != size-2:
                raise ValueError('Truncated JPEG segment')
            if marker[0] in (0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf):
                if len(body) < 5:
                    raise ValueError('Invalid JPEG frame')
                height, width = struct.unpack('>HH', body[1:5])
            if marker[0] == 0xe1 and body.startswith(b'Exif\0\0'):
                tiff = body[6:]
                try:
                    order = {'II':'<','MM':'>'}[tiff[:2].decode('ascii')]
                    offset = struct.unpack_from(order+'I', tiff, 4)[0]
                    count = struct.unpack_from(order+'H', tiff, offset)[0]
                    for i in range(count):
                        at = offset+2+12*i
                        tag, kind, n = struct.unpack_from(order+'HHI', tiff, at)
                        if tag == 274 and kind == 3 and n == 1:
                            orientation = struct.unpack_from(order+'H', tiff, at+8)[0]
                except (KeyError, UnicodeError, struct.error):
                    raise ValueError('Cannot read EXIF orientation; normalize this JPEG first')
    if not width or not height or orientation not in range(1,9):
        raise ValueError('Invalid JPEG frame or orientation')
    return width, height, orientation


def scaffold(source, output, template, intensity=None, camera=None, sound=True, duration=None, fps=30):
    source, output = Path(source).resolve(), Path(output).resolve()
    width, height, extension, orientation = image_info(source)
    if output.exists():
        raise ValueError(f'Output already exists: {output}. Choose a new directory.')
    skill = Path(__file__).resolve().parents[1]
    templates = {'cards': 'card-impact', 'icons': 'desktop-gravity', 'photo': 'photo-parallax'}
    if template not in templates:
        raise ValueError('Unknown template.')
    if template != 'photo' and (intensity is not None or camera is not None or not sound or duration is not None):
        raise ValueError('Profile options currently apply to photo; adapt cards/icons in build.py.')
    if intensity not in (None,'subtle','balanced','strong') or camera not in (None,'static','cinematic','dynamic'):
        raise ValueError('Unknown intensity or camera mode')
    if not isinstance(fps,int) or isinstance(fps,bool) or not 1 <= fps <= 60:
        raise ValueError('fps must be an integer from 1 to 60')
    duration = duration if duration is not None else (20 if template == 'icons' else 18)
    if not isinstance(duration,(int,float)) or isinstance(duration,bool) or not 2 <= duration <= 60:
        raise ValueError('duration must be 2–60 seconds')
    if template == 'photo' and ((width + width % 2) > 4096 or (height + height % 2) > 4096):
        raise ValueError('Photo source exceeds the 4096-pixel template limit; choose a renderer that supports its native size instead of silently downsizing.')
    output.mkdir(parents=True)
    source_name = 'source'+extension
    shutil.copy2(source, output / source_name)
    shutil.copy2(skill / 'assets' / templates[template] / 'build.py', output / 'build.py')
    if template != 'photo' and extension != '.png':
        builder = output / 'build.py'
        builder.write_text(builder.read_text(encoding='utf-8').replace('source.png', source_name), encoding='utf-8')
    shutil.copy2(skill / 'assets' / 'prepare.mjs', output / 'prepare.mjs')
    package = {'name': 'screenshot-motion-project', 'version': '0.1.0', 'private': True, 'type': 'module',
               'engines': {'node': '>=22'},
               'scripts': {'prepare': 'node prepare.mjs', 'doctor': 'hyperframes doctor', 'check': 'hyperframes check',
                           'preview': 'hyperframes preview --background', 'render': f'hyperframes render --output demo.mp4 --fps {fps} --quality high'},
               'dependencies': {'gsap': '3.14.2', 'hyperframes': '0.8.34'}}
    (output / 'package.json').write_text(json.dumps(package, indent=2) + '\n', encoding='utf-8')
    metadata = {'source_size': [width, height], 'source_file':source_name, 'orientation':orientation, 'template': template, 'requires_layout_adaptation': True}
    (output / 'source-info.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    # A one-pixel even-dimension pad is permitted for video encoders; keep the source pixels.
    ow = width + width % 2 if template == 'photo' else 1080
    oh = height + height % 2 if template == 'photo' else min(4096, max(2, round(ow*height/width/2)*2))
    plan = {'version':1,'source':{'file':source_name,'width':width,'height':height,'orientation':orientation},
            'output':{'width':ow,'height':oh,'duration':duration,'fps':fps},
            'style':{'intensity':intensity or 'strong','camera':camera or 'dynamic','sound':sound,'seed':19},
            'layers':[],'patches':[],'lights':[]}
    (output/'motion-plan.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    (output / '.gitignore').write_text('node_modules/\n*.mp4\n*.wav\nsnapshots/\n.hyperframes/\n', encoding='utf-8')
    (output / 'DESIGN.md').write_text(f'# Screenshot motion\n\nSource: {width} × {height}.\n\nBefore building: inspect the screenshot and adapt build.py crop coordinates, design dimensions, labels, colors and timeline. The selected template uses example-specific geometry.\n', encoding='utf-8')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--template', choices=['cards', 'icons', 'photo'], required=True)
    parser.add_argument('--intensity', choices=['subtle','balanced','strong'])
    parser.add_argument('--camera', choices=['static','cinematic','dynamic'])
    parser.add_argument('--no-sound', action='store_true')
    parser.add_argument('--duration', type=float)
    parser.add_argument('--fps', type=int, default=30)
    args = parser.parse_args()
    try:
        path = scaffold(args.source, args.output, args.template,args.intensity,args.camera,not args.no_sound,args.duration,args.fps)
        print(f'Created: {path}\nAdapt build.py (cards/icons) or motion-plan.json (photo) to the image.\nThen: npm install; python build.py; npm run check; npm run render')
    except (ValueError, OSError) as exc:
        parser.exit(1, f'{exc}\n')

import importlib.util
import json
from pathlib import Path
import struct
import math
import random
import wave
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


installer = load('installer', ROOT / 'scripts/install.py')
creator = load('creator', ROOT / 'skills/screenshot-impact-video/scripts/scaffold.py')
photo = load('photo', ROOT / 'skills/screenshot-impact-video/assets/photo-parallax/build.py')


class PackagingTests(unittest.TestCase):
    @staticmethod
    def rgba_png(path, width, height):
        def chunk(kind, payload):
            return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff)
        pixels = bytearray()
        for y in range(height):
            pixels.append(0)
            for x in range(width):
                pixels.extend((x % 256, y % 256, (x ^ y) % 256, 64 + (x + y) % 160))
        payload = b'\x89PNG\r\n\x1a\n'
        payload += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
        payload += chunk(b'IDAT', zlib.compress(bytes(pixels)))
        payload += chunk(b'IEND', b'')
        path.write_bytes(payload)

    def test_installs_complete_skill_and_preserves_existing(self):
        with tempfile.TemporaryDirectory() as temp:
            target = installer.install(temp)
            self.assertTrue((target / 'assets/desktop-gravity/build.py').is_file())
            marker = target / 'custom.txt'
            marker.write_text('keep')
            with self.assertRaises(ValueError):
                installer.install(temp)
            self.assertEqual(marker.read_text(), 'keep')

    def test_scaffold_keeps_source_and_marks_layout_adaptation(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / 'source.png'
            source.write_bytes(b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR' + struct.pack('>II', 900, 600))
            for style in ('cards', 'icons'):
                output = creator.scaffold(source, base / style, style)
                self.assertEqual((output / 'source.png').read_bytes(), source.read_bytes())
                info = json.loads((output / 'source-info.json').read_text())
                self.assertEqual(info['source_size'], [900, 600])
                self.assertTrue(info['requires_layout_adaptation'])
                pkg = json.loads((output / 'package.json').read_text())
                self.assertEqual(pkg['dependencies']['hyperframes'], '0.8.34')
                self.assertTrue((output / 'prepare.mjs').is_file())
                with self.assertRaises(ValueError):
                    creator.scaffold(source, output, style)

    def test_bad_source_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / 'bad.png'
            source.write_text('not a PNG')
            output = base / 'output'
            with self.assertRaises(ValueError):
                creator.scaffold(source, output, 'cards')
            self.assertFalse(output.exists())

    def test_photo_defaults_keep_native_pixels_or_fail_before_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / 'source.png'
            source.write_bytes(b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR' + struct.pack('>II', 1920, 1080))
            out = creator.scaffold(source, base / 'native', 'photo')
            plan = json.loads((out / 'motion-plan.json').read_text())
            self.assertEqual((plan['output']['width'], plan['output']['height']), (1920, 1080))
            oversized = base / 'oversized.png'
            oversized.write_bytes(b'\x89PNG\r\n\x1a\n' + struct.pack('>I', 13) + b'IHDR' + struct.pack('>II', 5000, 3000))
            with self.assertRaisesRegex(ValueError, 'native size'):
                creator.scaffold(oversized, base / 'oversized-output', 'photo')
            self.assertFalse((base / 'oversized-output').exists())

    def test_jpeg_format_and_orientation_are_read_from_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'wrong-extension.png'
            tiff = b'II'+struct.pack('<HIH',42,8,1)+struct.pack('<HHI',274,3,1)+struct.pack('<H',6)+b'\0\0'+b'\0'*4
            exif = b'Exif\0\0'+tiff
            frame = b'\x08'+struct.pack('>HH',640,480)+b'\x01\x01\x11\x00'
            path.write_bytes(b'\xff\xd8\xff\xe1'+struct.pack('>H',len(exif)+2)+exif+b'\xff\xc0'+struct.pack('>H',len(frame)+2)+frame+b'\xff\xd9')
            self.assertEqual(creator.image_info(path),(480,640,'.jpg',6))
            out = creator.scaffold(path,Path(temp)/'project','photo')
            self.assertTrue((out/'source.jpg').is_file())
            with self.assertRaisesRegex(ValueError,'EXIF'):
                photo.build(out)

    def test_photo_profile_changes_real_output_and_sound(self):
        with tempfile.TemporaryDirectory() as temp:
            out = creator.scaffold(ROOT/'demo-source.png',Path(temp)/'project','photo',intensity='subtle',camera='static',sound=False,duration=2,fps=24)
            photo.build(out)
            page = (out/'index.html').read_text()
            self.assertNotIn('<audio',page)
            self.assertNotIn("tl.to('.camera'",page)
            self.assertIn('data-duration="2"',page)
            self.assertIn('--fps 24',json.loads((out/'package.json').read_text())['scripts']['render'])
            plan = json.loads((out/'motion-plan.json').read_text())
            plan['style'].update(camera='dynamic',sound=True)
            plan['layers']=[{'id':'subject','rect':[104,214,246,137],'dx':-35,'dy':-60}]
            (out/'motion-plan.json').write_text(json.dumps(plan))
            photo.build(out)
            page = (out/'index.html').read_text()
            self.assertIn("tl.to('#subject'",page)
            self.assertIn("tl.to('.camera'",page)
            with wave.open(str(out/'impact.wav')) as sound:
                self.assertEqual(sound.getnframes()/sound.getframerate(),2)
            plan['layers'][0]['rect']=[1150,0,100,100]
            (out/'motion-plan.json').write_text(json.dumps(plan))
            with self.assertRaisesRegex(ValueError,'inside'):
                photo.build(out)

    def test_photo_alpha_cutout_and_patch_mask_are_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            out = creator.scaffold(ROOT/'demo-source.png',Path(temp)/'project','photo',sound=False,duration=2)
            self.rgba_png(out/'subject.png', 100, 80)
            self.rgba_png(out/'patch-mask.png', 1180, 730)
            (out/'clean-plate.png').write_bytes((out/'source.png').read_bytes())
            plan = json.loads((out/'motion-plan.json').read_text())
            plan['layers'] = [{'id':'subject','rect':[20,30,100,80],'cutout':'subject.png','start':.4}]
            plan['patches'] = [{'file':'clean-plate.png','rect':[15,25,110,90],'mask':'patch-mask.png','start':.3}]
            (out/'motion-plan.json').write_text(json.dumps(plan))
            photo.build(out)
            page = (out/'index.html').read_text()
            self.assertIn('src="subject.png"', page)
            self.assertIn('mask-image:url(&quot;patch-mask.png&quot;)', page)
            self.rgba_png(out/'subject.png', 101, 80)
            with self.assertRaisesRegex(ValueError, '100x80'):
                photo.build(out)

    def test_camera_keeps_viewport_inside_rotated_image(self):
        rng = random.Random(42)
        for _ in range(150):
            w,h=rng.randint(300,2000),rng.randint(300,2000)
            pose=photo.camera_pose(w,h,rng.uniform(1,1.8),rng.uniform(-9,9),[rng.random(),rng.random()])
            a=math.radians(pose['rotation']);c,s=math.cos(a),math.sin(a)
            for x,y in [(-w/2,-h/2),(-w/2,h/2),(w/2,-h/2),(w/2,h/2)]:
                vx,vy=x-pose['x'],y-pose['y']
                ox,oy=(c*vx+s*vy)/pose['scale'],(-s*vx+c*vy)/pose['scale']
                self.assertLessEqual(abs(ox),w/2+1e-6)
                self.assertLessEqual(abs(oy),h/2+1e-6)


if __name__ == '__main__':
    unittest.main()

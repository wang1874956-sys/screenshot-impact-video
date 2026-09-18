"""Fail closed when a render silently loses source pixels or video frame rate."""

import argparse
from fractions import Fraction
import json
from pathlib import Path
import shutil
import subprocess

from scaffold import image_info


def probe(path, ffprobe):
    result = subprocess.run(
        [ffprobe, '-v', 'error', '-show_entries',
         'stream=codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,nb_frames',
         '-show_entries', 'format=duration,size', '-of', 'json', str(path)],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    video = next((s for s in data.get('streams', []) if s.get('codec_type') == 'video'), None)
    if not video:
        raise ValueError(f'No video stream: {path}')
    fps = None
    # r_frame_rate is the nominal capture cadence; avg_frame_rate can drift
    # slightly after a recording ends between exact frame boundaries.
    for rate in (video.get('r_frame_rate'), video.get('avg_frame_rate')):
        try:
            candidate = Fraction(rate)
            if candidate > 0:
                fps = candidate
                break
        except (TypeError, ValueError, ZeroDivisionError):
            pass
    if fps is None:
        raise ValueError(f'Unknown frame rate: {path}')
    return {
        'width': video['width'], 'height': video['height'],
        'fps': fps, 'frames': video.get('nb_frames'),
        'duration': data.get('format', {}).get('duration'),
        'video_codec': video.get('codec_name'),
        'audio': any(s.get('codec_type') == 'audio' for s in data.get('streams', [])),
    }


def verify(source, output, kind, ffprobe, allow_resize=False, allow_fps_change=False):
    source, output = Path(source), Path(output)
    if kind == 'photo':
        width, height, _, _ = image_info(source)
        expected_size = (width + width % 2, height + height % 2)
        expected_fps = None
    else:
        original = probe(source, ffprobe)
        expected_size = (original['width'], original['height'])
        expected_fps = original['fps']
    rendered = probe(output, ffprobe)
    actual_size = (rendered['width'], rendered['height'])
    errors = []
    if actual_size != expected_size and not allow_resize:
        errors.append(f'dimensions: source {expected_size}, output {actual_size}')
    if expected_fps and rendered['fps'] != expected_fps and not allow_fps_change:
        errors.append(f'frame rate: source {expected_fps}, output {rendered["fps"]}')
    return rendered, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--kind', required=True, choices=('photo', 'video'))
    parser.add_argument('--ffprobe', default=shutil.which('ffprobe'))
    parser.add_argument('--allow-resize', action='store_true', help='Only after a deliberate canvas choice')
    parser.add_argument('--allow-fps-change', action='store_true', help='Only after a deliberate frame-rate choice')
    args = parser.parse_args()
    if not args.ffprobe:
        parser.error('ffprobe is required; pass --ffprobe with its local executable path')
    try:
        rendered, errors = verify(args.source, args.output, args.kind, args.ffprobe,
                                  args.allow_resize, args.allow_fps_change)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'Verification failed: {exc}\n')
    print(f'{rendered["width"]}x{rendered["height"]} {rendered["fps"]} fps; '
          f'{rendered["frames"] or "?"} frames; audio={rendered["audio"]}; '
          f'{rendered["video_codec"]}')
    if errors:
        parser.exit(1, 'Unapproved quality reduction: ' + '; '.join(errors) + '\n')
    print('Source dimensions preserved' + ('; source video frame rate preserved.' if args.kind == 'video' else '.'))


if __name__ == '__main__':
    main()

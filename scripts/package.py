"""Build a shareable repository ZIP from an explicit public file allowlist."""
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
archive = root / 'screenshot-impact-video.zip'
files = []
for name in ('README.md', '.gitignore', 'photo-plan.md', 'demo.mp4', 'demo-source.png', 'preview.gif'):
    path = root / name
    if not path.is_file():
        raise FileNotFoundError(path)
    files.append(path)
for name in ('skills', 'scripts', 'tests'):
    for path in (root / name).rglob('*'):
        if (path.is_file() and '__pycache__' not in path.parts
                and path.suffix != '.pyc' and path.name != 'gsap.min.js'):
            files.append(path)
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as output:
    for path in sorted(files):
        output.write(path, Path('screenshot-impact-video') / path.relative_to(root))
print(f'Packaged {len(files)} public files: {archive}')

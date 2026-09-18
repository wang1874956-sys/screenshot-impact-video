"""Install the bundled Codex skill without overwriting an existing installation."""
import argparse
import os
from pathlib import Path
import shutil


def install(target_root=None):
    source = Path(__file__).resolve().parents[1] / 'skills' / 'screenshot-impact-video'
    root = Path(target_root).expanduser() if target_root else Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'skills'
    target = root.resolve() / source.name
    if target.exists():
        raise ValueError(f'Skill already exists: {target}. Back it up or choose --target before installing.')
    if not (source / 'SKILL.md').is_file():
        raise ValueError('Skill files are missing. Download the complete repository first.')
    root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', help='Parent skill directory; defaults to CODEX_HOME/skills or ~/.codex/skills')
    args = parser.parse_args()
    try:
        print(f'Installed: {install(args.target)}')
        print('Invoke $screenshot-impact-video with a screenshot in Codex. Refresh the skill list if needed.')
    except (ValueError, OSError) as exc:
        parser.exit(1, f'{exc}\n')

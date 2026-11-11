"""Isolated paths for the two installed OpenCode versions."""
import os
from pathlib import Path

LAB = Path('/tmp/opencode-lab')
ROOT = Path(__file__).resolve().parents[1]


def environment(version):
    env = os.environ.copy()
    base = LAB / f'home-v{version}'
    for name, folder in [('XDG_CONFIG_HOME', 'config'), ('XDG_DATA_HOME', 'data'),
                         ('XDG_CACHE_HOME', 'cache'), ('XDG_STATE_HOME', 'state')]:
        path = base / folder
        path.mkdir(parents=True, exist_ok=True)
        env[name] = str(path)
    env['OPENCODE_TEST_HOME'] = str(base)
    env['PATH'] = f"{LAB}/runtime/bun-linux-x64:{env.get('PATH', '')}"
    if version == 1 and os.getenv('LAB_V1_BACKGROUND') == '1':
        env['OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS'] = 'true'
    env['OPENCODE_DISABLE_AUTOUPDATE'] = 'true'
    return env


def binary(version):
    return str(LAB / f'v{version}/package/bin/opencode')

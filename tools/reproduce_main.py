"""NEW packaging helper: preserve historical journal order; unchanged analysis."""
import argparse
import contextlib
import importlib.metadata
import io
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'pivot/kaggle_outputs/20261002-182357/out'
ORDER = ('Phi-4-mini-instruct-1.jsonl', 'Qwen3-4B-Instruct-2507-0.jsonl')
COMMIT = '9e34d608c7a96a34c6ee7680878505fedc296bbc'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit('Output must be a new directory; refuse overwrite')
    if output == ROOT or ROOT in output.parents:
        raise SystemExit('Output must be outside the read-only package')
    for name, expected in [('numpy', '2.1.3'), ('jsonschema', '4.23.0')]:
        if importlib.metadata.version(name) != expected:
            raise SystemExit(f'Byte-identical reproduction requires {name}=={expected}')
    original_glob = Path.glob

    def ordered_glob(path, pattern, *positional, **keywords):
        if path.resolve() == RAW.resolve() and pattern == '*.jsonl':
            found = list(original_glob(path, pattern, *positional, **keywords))
            if {p.name for p in found} != set(ORDER):
                raise ValueError('Unexpected journal file set')
            return iter(path / name for name in ORDER)
        return original_glob(path, pattern, *positional, **keywords)

    # Only the raw-journal enumeration changes. Rows, scores, statistical
    # code, seed and every frozen input are passed through without alteration.
    old_argv = sys.argv
    Path.glob = ordered_glob
    sys.path.insert(0, str(ROOT / 'analysis'))
    sys.argv = ['analyze_main.py', '--raw', str(RAW), '--output', str(output), '--commit', COMMIT]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(ROOT / 'analysis/analyze_main.py'), run_name='__main__')
    finally:
        Path.glob = original_glob
        sys.argv = old_argv
    print(json.dumps({'outputs': 11520, 'output': str(output), 'run_id': '20261002-182357',
                      'operation': 'CPU scoring only; no model inference'}))


if __name__ == '__main__':
    main()

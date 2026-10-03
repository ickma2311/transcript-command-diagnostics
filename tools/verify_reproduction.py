"""NEW packaging helper: verify all bytes, output identities and row count."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    pairs = {}
    for name in ['summary.json', 'scored.jsonl']:
        expected = ROOT / 'results/main' / name
        actual = out / name
        pairs[name] = {'expected_sha256': digest(expected), 'actual_sha256': digest(actual),
                       'byte_identical': expected.read_bytes() == actual.read_bytes()}
    original = [json.loads(line) for line in (ROOT / 'results/main/scored.jsonl').read_text().splitlines()]
    actual = [json.loads(line) for line in (out / 'scored.jsonl').read_text().splitlines()]
    key = lambda r: (r['model_id'], r['row_id'], r['prompt_id'])
    original_keys, actual_keys = list(map(key, original)), list(map(key, actual))
    inputs = [json.loads(line) for line in (ROOT / 'pivot/inputs/main.jsonl').read_text().splitlines()]
    models = json.loads((ROOT / 'pivot/configs/models.json').read_text())
    expected_keys = {(m['id'], r['row_id'], pid) for m in models for r in inputs for pid in [0, 1]}
    report = {'status': 'PASS', 'expected_outputs': len(expected_keys), 'actual_outputs': len(actual),
              'no_duplicate_keys': len(set(actual_keys)) == len(actual_keys),
              'complete_expected_keyset': set(actual_keys) == expected_keys,
              'original_keyset_equal': set(original_keys) == set(actual_keys),
              'original_row_order_equal': original_keys == actual_keys, 'files': pairs}
    if not (len(actual) == 11520 and report['no_duplicate_keys'] and report['complete_expected_keyset']
            and report['original_keyset_equal'] and report['original_row_order_equal']
            and all(value['byte_identical'] for value in pairs.values())):
        report['status'] = 'FAIL'
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()

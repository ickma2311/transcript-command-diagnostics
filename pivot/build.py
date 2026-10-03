"""Own A/R minimal pairs; reference state precedes all text/parser outputs."""
import copy
from functools import lru_cache
import hashlib
import itertools
import json
from pathlib import Path
import random

ROOT = Path(__file__).parent
V = {
    'development': {'names': 'adele boris celia dario emre farah grace henry imani jules keiko louis'.split(),
                    'items': 'pens folders notebooks envelopes clips boxes cards labels binders markers rulers erasers'.split(),
                    'codes': 'amber cobalt coral gold gray ivory navy ochre orange silver teal violet'.split(),
                    'days': 'monday tuesday wednesday'.split()},
    'test': {'names': 'nora oscar paula quinn ravi sonia talia umar vera wesley xenia yusuf'.split(),
             'items': 'tape ribbons paper staples trays stamps cushions plates towels mugs bottles bags'.split(),
             'codes': 'apricot indigo jade lilac maroon olive pearl plum ruby saffron scarlet walnut'.split(),
             'days': 'thursday friday saturday sunday'.split()},
}
NUMBER = 'one two three four five six seven eight nine'.split()
KEY = {'shopping': 'purchases', 'meeting': 'tasks', 'files': 'operations'}


def run_program(family, actions, prohibited, updates):
    # This is the latent reference executor. No text parsing informs this state.
    result = {KEY[family]: copy.deepcopy(actions), 'prohibited': [copy.deepcopy(prohibited)]}
    for index, field, value in updates:
        result[KEY[family]][index][field] = value
    return result


def body(record, family, style):
    if family == 'shopping':
        verb = ['buy', 'purchase', 'order', 'please order', 'get', 'obtain', 'acquire', 'please buy', 'please purchase', 'procure'][style]
        return f"{verb} {NUMBER[record['quantity']-1]} {record['item']} from {record['seller']}"
    if family == 'meeting':
        a, v, o = record['actor'], record['verb'], record['object']
        return [f'{a} will {v} {o}', f'assign {a} to {v} {o}', f'ask {a} to {v} {o}',
                f'have {a} {v} {o}', f'{a} should {v} {o}', f'{a} must {v} {o}',
                f'{a} needs to {v} {o}', f'let {a} {v} {o}', f'tell {a} to {v} {o}',
                f'{a} is to {v} {o}'][style]
    s, d = record['source'], record['destination']
    return [f'copy {s} to {d}', f'duplicate {s} as {d}', f'copy {s} into {d}',
            f'copy file {s} to {d}', f'copy the file {s} to {d}', f'make a copy of {s} named {d}',
            f'create a copy of {s} called {d}', f'make {d} a copy of {s}',
            f'duplicate file {s} as {d}', f'reproduce {s} under name {d}'][style]


def update_clause(update, family, split, style):
    index, field, value = update
    ordinal = ['first', 'second'][index]
    noun = {'shopping': 'purchase', 'meeting': 'task', 'files': 'operation'}[family]
    variant = style % 2 + (2 if split == 'test' else 0)
    return [f'set the {field} of the {ordinal} {noun} to {value}',
            f'for the {ordinal} {noun} use {field} {value}',
            f'update the {ordinal} {noun} so its {field} is {value}',
            f'the {ordinal} {noun} now has {field} {value}'][variant]


def make_pair(family, split, depth, style, replicate):
    seed = f'preimage-v4-{family}-{split}-d{depth}-s{style}-r{replicate}'
    rng = random.Random(int.from_bytes(hashlib.sha256(seed.encode()).digest()[:8], 'big'))
    vocab = V[split]
    names = rng.sample(vocab['names'], 4)
    items = rng.sample(vocab['items'], 3)
    codes = rng.sample(vocab['codes'], 7)
    day0, day1 = rng.sample(vocab['days'], 2)
    if family == 'shopping':
        actions = [{'item': items[i], 'quantity': rng.randrange(1, 10), 'seller': names[i], 'day': None} for i in range(2)]
        forbidden = {'verb': 'buy', 'object': items[-1]}
        field, values = 'seller', names[2:]
    elif family == 'meeting':
        actions = [{'actor': names[i], 'verb': rng.choice(['pack', 'label', 'ship', 'check']), 'object': codes[i], 'day': None} for i in range(2)]
        forbidden = {'verb': 'email', 'object': codes[-1]}
        field, values = 'actor', names[2:]
    else:
        actions = [{'verb': 'copy', 'source': codes[i], 'destination': codes[i+2], 'day': None} for i in range(2)]
        forbidden = {'verb': 'change', 'object': codes[-1]}
        field, values = 'destination', codes[4:6]
    # Balance the chosen A latent attachment within each style/depth stratum.
    attachment = (replicate + style) % 2
    target = rng.randrange(2)
    updates = [(target, field, values[u]) for u in range(depth)]
    cores = [body(record, family, style) for record in actions]
    prohibition = [('do not' if style % 2 == 0 else 'never') if split == 'development'
                   else ('you must not' if style % 2 == 0 else 'it is forbidden to')][0]
    policy = f"{prohibition} {forbidden['verb']} {forbidden['object']}"
    tails = [policy] + [update_clause(u, family, split, style) for u in updates]
    pair_id = f'{split}-{family}-d{depth}-s{style}-r{replicate}'
    records = []
    for item_type in ['A', 'R']:
        latent = copy.deepcopy(actions)
        if item_type == 'A':
            latent[attachment]['day'] = day1
            clauses = [cores[0] + ' on ' + day1, cores[1]] if attachment == 0 else [cores[0], 'on ' + day1 + ' ' + cores[1]]
            alternative = copy.deepcopy(actions)
            alternative[1-attachment]['day'] = day1
            alternative_clauses = [cores[0], 'on ' + day1 + ' ' + cores[1]] if attachment == 0 else [cores[0] + ' on ' + day1, cores[1]]
            alternative_gold = run_program(family, alternative, forbidden, updates)
        else:
            # Match the forced R direction to A's latent direction, balanced
            # within each stratum. Never put two day phrases consecutively.
            if attachment == 1:
                latent[0]['day'], latent[1]['day'] = day0, day1
                clauses = ['on ' + day0 + ' ' + cores[0], 'on ' + day1 + ' ' + cores[1]]
            else:
                latent[0]['day'], latent[1]['day'] = day1, day0
                clauses = [cores[0] + ' on ' + day1, cores[1] + ' on ' + day0]
            alternative_clauses, alternative_gold = None, None
        gold = run_program(family, latent, forbidden, updates)
        records.append({'pair_id': pair_id, 'base_id': pair_id + '-' + item_type, 'family': family,
                        'split': split, 'depth': depth, 'style': style, 'replicate': replicate,
                        'template_id': f'{family}-{split}-style{style}', 'item_type': item_type,
                        'stratum': f'{family}-d{depth}', 'seed': seed, 'attachment': attachment,
                        'junction_day': day1,
                        'latent_program': {'actions': latent, 'prohibited': forbidden, 'updates': updates},
                        'clauses': clauses + tails, 'gold': gold,
                        'alternative_cued': ('.\n'.join(alternative_clauses + tails) + '.') if alternative_clauses else None,
                        'alternative_gold': alternative_gold})
    return records


def render(item, layout, filler):
    clauses = list(item['clauses'])
    if filler != 'none':
        marker = 'on ' + item['junction_day']
        replacement = 'uh ' + marker if filler == 'before' else marker + ' uh'
        # The junction phrase appears exactly once. No fillers elsewhere.
        assert sum(c.count(marker) for c in clauses) == 1
        clauses = [c.replace(marker, replacement) for c in clauses]
    text = '.\n'.join(clauses) + '.' if layout == 'cued' else ' '.join(clauses)
    if layout == 'misplaced':
        # Soft line breaks one word after each true clause boundary, while
        # periods remain absent. Full context/words stay identical to uncued.
        words = text.split()
        gaps, cumulative = [], 0
        for clause in clauses[:-1]:
            cumulative += len(clause.split())
            gaps.append(cumulative + 1)
        text = ''.join(w + ('\n' if i + 1 in gaps else ' ') for i, w in enumerate(words)).strip()
    return text


def signature(state):
    return json.dumps(state, sort_keys=True)


def main():
    import regex_parser
    import earley_parser
    from scoring import state_valid
    comparisons = 0
    collision_proofs = 0
    summary = {}
    for key in V['development']:
        assert not set(V['development'][key]) & set(V['test'][key])
    for split, styles, replicates in [('development', range(2), range(6)), ('test', range(2, 10), range(10))]:
        items, rows = [], []
        for family, depth, style, replicate in itertools.product(KEY, [0], styles, replicates):
            for item in make_pair(family, split, depth, style, replicate):
                assert state_valid(item['gold'], family)
                items.append(item)
                if item['item_type'] == 'A':
                    proof_uncued = item['alternative_cued'].replace('.', '').replace('\n', ' ')
                    assert proof_uncued == render(item, 'uncued', 'none')
                    alternative_readings = earley_parser.readings(item['alternative_cued'], family)
                    assert len(alternative_readings) == 1 and alternative_readings[0] == item['alternative_gold']
                    assert item['alternative_gold'] != item['gold']
                    collision_proofs += 1
                cells = list(itertools.product(['cued', 'uncued'], ['none', 'before', 'after']))
                for layout, filler in cells:
                    text = render(item, layout, filler)
                    a, b = regex_parser.readings(text, family), earley_parser.readings(text, family)
                    sa, sb = {signature(s) for s in a}, {signature(s) for s in b}
                    expected = 2 if item['item_type'] == 'A' and layout != 'cued' else 1
                    assert len(a) == expected and sa == sb and signature(item['gold']) in sa, (item['base_id'], layout, filler, a, b)
                    if expected == 2:
                        assert signature(item['alternative_gold']) in sa
                    assert text == text.lower()
                    no_fillers = [w for w in text.replace('.', '').split() if w not in {'um', 'uh'}]
                    assert no_fillers == ' '.join(item['clauses']).split()
                    pause_tokens = text.replace('.', '').split()
                    assert pause_tokens.count('um') + pause_tokens.count('uh') == (1 if filler != 'none' else 0)
                    assert all(state_valid(s, family) for s in a)
                    comparisons += 1
                    rows.append({k: item[k] for k in ['pair_id', 'base_id', 'family', 'split', 'depth', 'style', 'replicate', 'template_id', 'item_type', 'stratum', 'attachment', 'junction_day', 'gold']} |
                                {'row_id': f"{item['base_id']}-{layout}-F{filler}", 'text': text, 'layout': layout, 'filler': filler,
                                 'readings': sorted(a, key=signature), 'reading_count': len(a),
                                 'asr': 'not_measured', 'human_annotation': 'not_performed'})
        if len({row['text'] for row in rows}) != len(rows):
            raise ValueError('Duplicate model-visible text within split; no freeze/inference')
        for filename, contents in [(split + '_items.jsonl', items), (split + '.jsonl', rows)]:
            (ROOT / 'inputs' / filename).write_text(''.join(json.dumps(r) + '\n' for r in contents))
        summary[split] = {'pairs': len(items)//2, 'items': len(items), 'rows': len(rows), 'surface_frames': len(styles)*3,
                          'sha256': hashlib.sha256((ROOT/'inputs'/f'{split}.jsonl').read_bytes()).hexdigest()}
    result = {'version': 'v4-constrained-direct-candidate', 'frozen': False, 'dual_parser_cell_comparisons': comparisons,
              'counterfactual_collision_proofs': collision_proofs, 'all_reading_sets_equal': True,
              'latent_inclusion': True, 'disjoint_identifier_vocab': True, 'all_lowercase': True,
              'model_visible_texts_unique_within_split': True,
              'summaries': summary, 'models_run': 0, 'scope': 'declared command grammar, not human naturalness/ambiguity'}
    (ROOT.parent/'protocol/PIVOT_DATA_VALIDATION.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()

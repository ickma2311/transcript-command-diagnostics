"""Input-relative state evaluation with fixed library-validated schemas."""
from functools import lru_cache
import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).parent


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('Duplicate JSON key')
        value[key] = item
    return value


def parse(text):
    wrapped = False
    candidate = text.strip()
    if candidate.startswith('```'):
        lines = candidate.splitlines()
        if len(lines) < 3 or lines[0].lower() not in {'```', '```json'} or lines[-1] != '```':
            return None, False
        candidate = '\n'.join(lines[1:-1])
        wrapped = True
    try:
        def reject_constant(value):
            raise ValueError('Nonfinite JSON number')
        value = json.loads(candidate, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except (TypeError, ValueError):
        return None, wrapped
    return (value if isinstance(value, dict) else None), wrapped


def canonical(value):
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, list):
        return [canonical(v) for v in value]
    if isinstance(value, dict):
        result = {k: canonical(v) for k, v in value.items()}
        if isinstance(result.get('prohibited'), list):
            result['prohibited'] = sorted(result['prohibited'], key=lambda v: json.dumps(v, sort_keys=True))
        return result
    if type(value) is float and value.is_integer():
        return int(value)
    return value


@lru_cache(None)
def validator(family, kind):
    schema = json.loads((ROOT/'configs'/f'{family}-{kind}.json').read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def state_valid(state, family):
    return validator(family, 'state').is_valid(canonical(state))


def state_signature(state):
    return json.dumps(canonical(state), sort_keys=True, separators=(',', ':'))


def score(text, row):
    value, wrapped = parse(text)
    diagnostic_default = False if len(row['readings']) == 1 else None
    result = {'json_parsed': value is not None, 'wrapped': wrapped,
              'schema_valid': False,
              'latent_state_match': False, 'admissible_commitment': False,
              'right_commitment': False, 'left_commitment': False,
              'junction_slots_match': diagnostic_default, 'other_slots_match': diagnostic_default,
              'category': 'L0_parse'}
    if value is None:
        return result
    normalized = canonical(value)
    if not state_valid(normalized, row['family']):
        result['category'] = 'L1_schema'
        return result
    result['schema_valid'] = True
    allowed = {state_signature(v) for v in row['readings']}
    predicted = state_signature(normalized)
    admissible = predicted in allowed
    latent = predicted == state_signature(row['gold'])
    key = {'shopping': 'purchases', 'meeting': 'tasks', 'files': 'operations'}[row['family']]
    records = normalized[key]
    gold = canonical(row['gold'])
    # Decompose day binding vs other fields. A schema-valid but missing/extra
    # action cannot silently receive full non-day credit.
    same_count = len(records) == len(gold[key])
    day_match = same_count and [v['day'] for v in records] == [v['day'] for v in gold[key]]
    other_match = same_count and normalized['prohibited'] == gold['prohibited'] and all(
        {k: v for k, v in a.items() if k != 'day'} == {k: v for k, v in b.items() if k != 'day'}
        for a, b in zip(records, gold[key]))
    right = admissible and len(records) == 2 and records[1]['day'] == row['junction_day']
    left = admissible and len(records) == 2 and records[0]['day'] == row['junction_day']
    result.update(admissible_commitment=admissible, latent_state_match=latent,
                  right_commitment=right, left_commitment=left,
                  junction_slots_match=day_match if len(allowed) == 1 else None,
                  other_slots_match=other_match if len(allowed) == 1 else None,
                  category='L4_latent' if latent else 'L3_licensed_alternate' if admissible else 'L2_outside_readings')
    return result


CONTRACT = {
    'shopping': 'STATE={"purchases":[{"item":string,"quantity":integer,"seller":string,"day":string or null}],"prohibited":[{"verb":"buy","object":string}]}. Treat buy, purchase, order, get, obtain, acquire and procure as purchase requests. Copy item and seller identifiers.',
    'meeting': 'STATE={"tasks":[{"actor":string,"verb":string,"object":string,"day":string or null}],"prohibited":[{"verb":"email","object":string}]}. Positive verbs are pack,label,ship,check. Copy actor and object identifiers.',
    'files': 'STATE={"operations":[{"verb":"copy","source":string,"destination":string,"day":string or null}],"prohibited":[{"verb":"change","object":string}]}. Copy/duplicate/reproduce or make/create a copy mean copy. Copy source and destination identifiers.',
}


def messages(row, prompt_id):
    preamble = ['Extract one final requested task state from this controlled dictation.',
                'Read the controlled dictation and report one requested end state.'][prompt_id]
    rules = (" The language permits each positive command to have zero or one 'on DAY' modifier, placed before or after that command. "
             "A command cannot have two day modifiers. A period ends a command and prevents a modifier attaching across it. "
             "Newlines are whitespace and do not by themselves force command boundaries. "
             "A day modifier belongs to exactly one command and is never shared between commands. "
             "Day is the lowercase weekday name only (for example monday), without 'on'; "
             "use day null when a command has no day modifier and never infer a date. "
             "List positive actions in mention order. Put do-not/must-not/never/forbidden commands only in prohibited, with verb and object identifier separately. "
             "Ignore filled pauses um and uh. "
             "Identifiers are case-insensitive. "
             "Choose one state and use exactly the STATE schema keys; no omitted fields or extra explanation. "
             "Return only one JSON object. ")
    return [{'role': 'system', 'content': preamble + rules + CONTRACT[row['family']]},
            {'role': 'user', 'content': 'Dictation:\n' + row['text']}]

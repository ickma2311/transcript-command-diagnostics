"""Complete-production parser for input-relative scheduled-command states.

Independent implementation from earley_parser.py; does not import the builder,
latent gold, rendering code, or the Earley grammar/semantic interpreter.
"""
import copy
from functools import lru_cache
import json
import re

KEY = {"shopping": "purchases", "meeting": "tasks", "files": "operations"}
NUM = dict(zip("one two three four five six seven eight nine".split(), range(1, 10)))
ORD = {"first": 0, "second": 1}
DAY = r"(?P<day>monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
IDENT = lambda name: rf"(?P<{name}>[a-z]+)"


@lru_cache(None)
def productions(family):
    patterns = []

    def add(pattern, kind, meaning):
        patterns.append((re.compile(r"^(?:" + pattern + r")(?= |$|\.)"), kind, meaning))

    if family == "shopping":
        q = r"(?P<quantity>one|two|three|four|five|six|seven|eight|nine)"
        bodies = [rf"{verb} {q} {IDENT('item')} from {IDENT('seller')}"
                  for verb in ["buy", "purchase", "order", "please order", "get", "obtain",
                               "acquire", "please buy", "please purchase", "procure"]]

        def record(m):
            return {"item": m['item'], "quantity": NUM[m['quantity']], "seller": m['seller']}
    elif family == "meeting":
        a, v, o = IDENT('actor'), r"(?P<verb>pack|label|ship|check)", IDENT('object')
        bodies = [rf"{a} will {v} {o}", rf"assign {a} to {v} {o}", rf"ask {a} to {v} {o}",
                  rf"have {a} {v} {o}", rf"{a} should {v} {o}", rf"{a} must {v} {o}",
                  rf"{a} needs to {v} {o}", rf"let {a} {v} {o}", rf"tell {a} to {v} {o}",
                  rf"{a} is to {v} {o}"]

        def record(m):
            return {"actor": m['actor'], "verb": m['verb'], "object": m['object']}
    elif family == "files":
        s, d = IDENT('source'), IDENT('destination')
        bodies = [rf"copy {s} to {d}", rf"duplicate {s} as {d}", rf"copy {s} into {d}",
                  rf"copy file {s} to {d}", rf"copy the file {s} to {d}",
                  rf"make a copy of {s} named {d}", rf"create a copy of {s} called {d}",
                  rf"make {d} a copy of {s}", rf"duplicate file {s} as {d}",
                  rf"reproduce {s} under name {d}"]

        def record(m):
            return {"verb": "copy", "source": m['source'], "destination": m['destination']}
    else:
        raise ValueError(family)
    for body in bodies:
        add(body, "action", lambda m, r=record: dict(r(m), day=None))
        add("on " + DAY + " " + body, "action", lambda m, r=record: dict(r(m), day=m['day']))
        add(body + " on " + DAY, "action", lambda m, r=record: dict(r(m), day=m['day']))
    forbidden_verb = {"shopping": "buy", "meeting": "email", "files": "change"}[family]
    for prefix in ["do not", "never", "you must not", "it is forbidden to"]:
        add(rf"{prefix} {forbidden_verb} {IDENT('object')}", "prohibition",
            lambda m, verb=forbidden_verb: {"verb": verb, "object": m['object']})
    noun = {"shopping": "purchase", "meeting": "task", "files": "operation"}[family]
    field = {"shopping": "seller", "meeting": "actor", "files": "destination"}[family]
    ordinal = r"(?P<ordinal>first|second)"
    value = IDENT('value')
    for pattern in [rf"set the {field} of the {ordinal} {noun} to {value}",
                    rf"for the {ordinal} {noun} use {field} {value}",
                    rf"update the {ordinal} {noun} so its {field} is {value}",
                    rf"the {ordinal} {noun} now has {field} {value}"]:
        add(pattern, "update", lambda m, f=field: (ORD[m['ordinal']], f, m['value']))
    return patterns


def readings(text, family):
    # Reject out-of-language symbols instead of ignoring them.
    if re.search(r"[^a-zA-Z.\s]", text):
        return []
    normalized = " ".join(re.sub(r"\b(?:um|uh)\b", " ", text.lower()).split())
    if not normalized:
        return []
    states = {}
    visits = 0

    def walk(rest, state):
        nonlocal visits
        visits += 1
        if visits > 10000:
            raise ValueError("Enumeration limit; cannot certify reading set")
        for pattern, kind, meaning in productions(family):
            match = pattern.match(rest)
            if match is None:
                continue
            new = copy.deepcopy(state)
            value = meaning(match)
            if kind == "action":
                new[KEY[family]].append(value)
            elif kind == "prohibition":
                new['prohibited'].append(value)
            else:
                index, field, replacement = value
                if index >= len(new[KEY[family]]):
                    continue
                new[KEY[family]][index][field] = replacement
            tail = rest[match.end():].strip()
            if tail.startswith('.'):
                tail = tail[1:].strip()
            if not tail:
                states[json.dumps(new, sort_keys=True)] = new
            else:
                walk(tail, new)

    walk(normalized, {KEY[family]: [], 'prohibited': []})
    return list(states.values())

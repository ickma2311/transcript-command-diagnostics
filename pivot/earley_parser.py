"""Separate Earley grammar and state interpreter, not builder gold execution.

Shares only the declared language semantics, not production tables or parser
code. Both implementations are authored locally; independent-agent review
checks their agreement and blind spots. Not independent human validation.
"""
from functools import lru_cache
from itertools import product
import json
import re
from lark import Lark, Tree, Token
from lark.exceptions import UnexpectedInput

COMMON = r'''
start: statement ("."? statement)* "."?
?statement: core -> no_day
          | "on" DAY core -> before_day
          | core "on" DAY -> after_day
          | prohibition
          | update
DAY: /(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?![a-z])/
NAME: /[a-z]+(?![a-z])/
NUMBER: /(?:one|two|three|four|five|six|seven|eight|nine)(?![a-z])/
ORDER: /(?:first|second)(?![a-z])/
%ignore /[ \t\r\n]+/
'''
GRAMMARS = {
    'shopping': r'''
core: purchase_verb NUMBER NAME "from" NAME
purchase_verb: "buy" | "purchase" | "order" | "please" "order"
             | "get" | "obtain" | "acquire" | "please" "buy"
             | "please" "purchase" | "procure"
prohibition: prohibition_prefix "buy" NAME
update: "set" "the" "seller" "of" "the" ORDER "purchase" "to" NAME
      | "for" "the" ORDER "purchase" "use" "seller" NAME
      | "update" "the" ORDER "purchase" "so" "its" "seller" "is" NAME
      | "the" ORDER "purchase" "now" "has" "seller" NAME
''',
    'meeting': r'''
core: NAME "will" VERB NAME
    | "assign" NAME "to" VERB NAME
    | "ask" NAME "to" VERB NAME
    | "have" NAME VERB NAME
    | NAME "should" VERB NAME
    | NAME "must" VERB NAME
    | NAME "needs" "to" VERB NAME
    | "let" NAME VERB NAME
    | "tell" NAME "to" VERB NAME
    | NAME "is" "to" VERB NAME
VERB: /(?:pack|label|ship|check)(?![a-z])/
prohibition: prohibition_prefix "email" NAME
update: "set" "the" "actor" "of" "the" ORDER "task" "to" NAME
      | "for" "the" ORDER "task" "use" "actor" NAME
      | "update" "the" ORDER "task" "so" "its" "actor" "is" NAME
      | "the" ORDER "task" "now" "has" "actor" NAME
''',
    'files': r'''
core: "copy" NAME "to" NAME
    | "duplicate" NAME "as" NAME
    | "copy" NAME "into" NAME
    | "copy" "file" NAME "to" NAME
    | "copy" "the" "file" NAME "to" NAME
    | "make" "a" "copy" "of" NAME "named" NAME
    | "create" "a" "copy" "of" NAME "called" NAME
    | "make" NAME "a" "copy" "of" NAME -> reverse_copy
    | "duplicate" "file" NAME "as" NAME
    | "reproduce" NAME "under" "name" NAME
prohibition: prohibition_prefix "change" NAME
update: "set" "the" "destination" "of" "the" ORDER "operation" "to" NAME
      | "for" "the" ORDER "operation" "use" "destination" NAME
      | "update" "the" ORDER "operation" "so" "its" "destination" "is" NAME
      | "the" ORDER "operation" "now" "has" "destination" NAME
''',
}
PREFIX = r'''
prohibition_prefix: "do" "not" | "never" | "you" "must" "not" | "it" "is" "forbidden" "to"
'''


@lru_cache(None)
def parser(family):
    return Lark(COMMON + GRAMMARS[family] + PREFIX, parser='earley', lexer='dynamic_complete', ambiguity='explicit')


def expand(tree):
    if not isinstance(tree, Tree):
        yield tree
    elif tree.data == '_ambig':
        for child in tree.children:
            yield from expand(child)
    else:
        for children in product(*(list(expand(child)) for child in tree.children)):
            yield Tree(tree.data, list(children))


def interpretation(tree, family):
    key = {'shopping': 'purchases', 'meeting': 'tasks', 'files': 'operations'}[family]
    field = {'shopping': 'seller', 'meeting': 'actor', 'files': 'destination'}[family]
    forbidden = {'shopping': 'buy', 'meeting': 'email', 'files': 'change'}[family]
    state = {key: [], 'prohibited': []}
    numbers = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9}
    for statement in tree.children:
        if statement.data == 'prohibition':
            obj = next(str(t) for t in statement.children if isinstance(t, Token))
            state['prohibited'].append({'verb': forbidden, 'object': obj})
        elif statement.data == 'update':
            order, value = [str(t) for t in statement.children if isinstance(t, Token)]
            position = 0 if order == 'first' else 1
            if position >= len(state[key]):
                return None
            state[key][position][field] = value
        else:
            core = next(t for t in statement.children if isinstance(t, Tree))
            day = next((str(t) for t in statement.children if isinstance(t, Token)), None)
            values = [str(t) for t in core.children if isinstance(t, Token)]
            if family == 'shopping':
                quantity, item, seller = values
                record = {'item': item, 'quantity': numbers[quantity], 'seller': seller, 'day': day}
            elif family == 'meeting':
                actor, verb, obj = values
                record = {'actor': actor, 'verb': verb, 'object': obj, 'day': day}
            else:
                source, dest = values if core.data != 'reverse_copy' else values[::-1]
                record = {'verb': 'copy', 'source': source, 'destination': dest, 'day': day}
            state[key].append(record)
    return state


def readings(text, family):
    if re.search(r'[^a-zA-Z.\s]', text):
        return []
    text = ' '.join(re.sub(r'\b(?:um|uh)\b', ' ', text.lower()).split())
    # Pause-location cells have exactly the same normalized syntax. Cache the
    # grammar computation, but return new objects so callers cannot mutate it.
    return json.loads(cached_readings(text, family))


@lru_cache(maxsize=10000)
def cached_readings(text, family):
    try:
        forest = parser(family).parse(text)
    except UnexpectedInput:
        return '[]'
    results = {}
    for i, tree in enumerate(expand(forest)):
        if i > 10000:
            raise ValueError('Forest expansion limit; cannot certify complete set')
        state = interpretation(tree, family)
        if state is not None:
            results[json.dumps(state, sort_keys=True)] = state
    return json.dumps(list(results.values()))

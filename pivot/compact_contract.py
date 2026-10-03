"""Pinned xgrammar0.1.25 fixed separators: validate, never alter raw output."""
import json
from scoring import validator


def fixed_json_spacing(text):
    quoted = False
    for i, char in enumerate(text):
        if quoted:
            if char == '"':
                quoted = False
            elif not ('a' <= char <= 'z'):
                # All fixed keys/values are ASCII letter strings; escapes,
                # whitespace and other characters are not emitted by this grammar.
                return False
            continue
        if char == '"':
            quoted = True
        elif char in ',:':
            if i+1 >= len(text) or text[i+1] != ' ' or i+2 >= len(text) or text[i+2].isspace():
                return False
        elif char.isspace():
            if char != ' ' or i == 0 or text[i-1] not in ',:':
                return False
    return not quoted


def _integer_literals_only(value):
    if isinstance(value, dict):
        return all(_integer_literals_only(v) for v in value.values())
    if isinstance(value, list):
        return all(_integer_literals_only(v) for v in value)
    return type(value) is not float


def fixed_contract_checks(text, parsed, family):
    # Shared semantic domain; two INDEPENDENT serialization checks. Comparing
    # a separately serialized copy is not rewriting or rescuing the raw text.
    domain = (parsed is not None and validator(family, 'state').is_valid(parsed)
              and _integer_literals_only(parsed))
    lexical = domain and fixed_json_spacing(text)
    reference = domain and text == json.dumps(parsed, separators=(', ', ': '), ensure_ascii=False)
    return bool(lexical), bool(reference)


def engine_receipt_valid(receipt):
    lines = receipt.get('structured_engine_log_lines', {})
    return (receipt.get('structured_decoding') is True and receipt.get('structured_backend') == 'xgrammar'
            and receipt.get('structured_disable_any_whitespace') is True
            and isinstance(lines, dict) and len(lines) == 2
            and all(isinstance(line, str) and 'Initializing a V1 LLM engine' in line
                    and "backend='xgrammar'" in line and 'disable_fallback=True' in line
                    and 'disable_any_whitespace=True' in line for line in lines.values()))

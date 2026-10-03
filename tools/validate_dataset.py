"""Check retained reading sets against both original parser implementations."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'pivot'))
from regex_parser import readings as regex_readings
from earley_parser import readings as earley_readings
from scoring import state_signature

if __name__=='__main__':
    count=0
    for name in ['development.jsonl','main.jsonl']:
        rows=[json.loads(x) for x in (ROOT/'pivot/inputs'/name).read_text().splitlines()]
        ids=set()
        for row in rows:
            if row['row_id'] in ids:raise ValueError('Duplicate row_id')
            ids.add(row['row_id'])
            expected={state_signature(x) for x in row['readings']}
            if expected!={state_signature(x) for x in regex_readings(row['text'],row['family'])}:raise ValueError('Regex reading mismatch')
            if expected!={state_signature(x) for x in earley_readings(row['text'],row['family'])}:raise ValueError('Earley reading mismatch')
            n=2 if row['item_type']=='A' and row['layout']=='uncued' else 1
            if len(expected)!=n or row['reading_count']!=n or state_signature(row['gold']) not in expected:
                raise ValueError('Reading cardinality/reference mismatch')
            count+=1
    print(json.dumps({'verified_texts':count,'parser_agreement':True,'scope':'Declared command grammar; not human annotation or natural-English completeness'}))

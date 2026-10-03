"""Constructed examples showing reference matches, licensed alternatives and errors."""
import json
from pathlib import Path
from score_predictions import evaluate

ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    inputs=[json.loads(x) for x in (ROOT/'pivot/inputs/main.jsonl').read_text().splitlines()]
    predictions=[json.loads(x) for x in (ROOT/'examples/predictions.jsonl').read_text().splitlines()]
    result=evaluate(inputs,predictions)
    print('Constructed demonstration; these are not new model results.')
    for row in result['scored']:print(row['row_id'],row['category'])
    print(json.dumps(result['groups'],indent=2))

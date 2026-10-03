"""Convenience evaluation on declared reading sets; not the frozen strict-generation replay."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'pivot'))
from scoring import score

def evaluate(inputs, predictions):
    by_id={r['row_id']:r for r in inputs}
    if len(by_id)!=len(inputs): raise ValueError('Duplicate input row_id')
    seen=set(); groups=defaultdict(list); scored=[]
    for prediction in predictions:
        row_id=prediction['row_id']
        if row_id not in by_id: raise ValueError('Unknown input row_id: '+str(row_id))
        text=prediction['text']
        if not isinstance(text,str): raise ValueError('Prediction text must be a string')
        model=prediction.get('model_id','external'); prompt=prediction.get('prompt_id',0)
        if not isinstance(model,str) or type(prompt) is not int: raise ValueError('Invalid model_id or prompt_id')
        identity=(model,row_id,prompt)
        if identity in seen: raise ValueError('Duplicate prediction identity')
        seen.add(identity); row=by_id[row_id]; result=score(text,row)
        unique=len(row['readings'])==1
        record={'row_id':row_id,'model_id':model,'prompt_id':prompt,'unique_state_input':unique,
                'reference_agreement_is_correctness':unique,**result}
        groups[(model,prompt)].append(record);scored.append(record)
    summaries=[]
    for (model,prompt),rows in sorted(groups.items()):
        n=len(rows); unique=[x for x in rows if x['unique_state_input']]
        summaries.append({'model_id':model,'prompt_id':prompt,'evaluated_outputs':n,'input_pool_size':len(inputs),
                          'coverage':n/len(inputs) if inputs else None,'categories':dict(Counter(x['category'] for x in rows)),
                          'grammar_admissible':sum(x['admissible_commitment'] for x in rows),
                          'reference_matches':sum(x['latent_state_match'] for x in rows),
                          'unique_state_inputs':len(unique),
                          'unique_state_correct':sum(x['latent_state_match'] for x in unique),
                          'unique_state_accuracy':sum(x['latent_state_match'] for x in unique)/len(unique) if unique else None})
    return {'scope':'Convenience scorer: parse/canonicalization rules in pivot/scoring.py. Reference agreement on ambiguous inputs is not correctness; admissibility is not original-intent recovery. This is not a replication of historical inference.',
            'groups':summaries,'scored':scored}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',type=Path,default=ROOT/'pivot/inputs/main.jsonl')
    parser.add_argument('--predictions',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): raise SystemExit('Refuse to overwrite an existing output')
    load=lambda p:[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    result=evaluate(load(args.inputs),load(args.predictions))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'output':str(args.output),'groups':result['groups']}))

if __name__=='__main__': main()

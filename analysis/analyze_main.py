"""Recompute heldout endpoints from complete raw journals; no partial claims."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
from inference_stats import hierarchical, holm_four

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'pivot'))
from scoring import score, parse, validator
from compact_contract import fixed_contract_checks, engine_receipt_valid


def identity(rows):
    result = {(r['pair_id'], r['item_type'], r['layout'], r['filler']): r for r in rows}
    if len(result) != len(rows):
        raise ValueError('Repeated endpoint cell')
    return result


def primary(rows, depths, endpoint, eligible):
    if not eligible:
        return {'eligible': False, 'reason': 'Calibration capability/infrastructure gate', 'p_for_holm': 1.}
    rows = [r for r in rows if r['depth'] in depths]
    cells = identity(rows)
    pair_ids = sorted({r['pair_id'] for r in rows})
    differences = []
    admissibility = []
    transitions = Counter()
    for pair in pair_ids:
        if endpoint == 'E1':
            cued, uncued = [cells[(pair, 'R', layout, 'none')] for layout in ['cued', 'uncued']]
            delta = int(cued['latent_state_match'])-int(uncued['latent_state_match'])
            template = cued['template_id']
        else:
            before, after = [cells[(pair, 'A', 'uncued', filler)] for filler in ['before', 'after']]
            delta = int(before['right_commitment'])-int(after['right_commitment'])
            admissibility.append((before['admissible_commitment'], after['admissible_commitment']))
            template = before['template_id']
            classify = lambda r: 'right' if r['right_commitment'] else 'left' if r['left_commitment'] else 'invalid'
            transitions[classify(before)+'->'+classify(after)] += 1
        depth = cued['depth'] if endpoint == 'E1' else before['depth']
        differences.append((template, pair, depth, delta))
    result = hierarchical(differences)
    result.update(eligible=True, endpoint=endpoint, depths=depths,
                  p_for_holm=result['p_raw_centered'], inference_status='approximate_empirical_bootstrap')
    if result['bootstrap_degenerate']:
        result.update(inference_status='descriptive_only_degenerate_bootstrap', p_for_holm=1.)
    if endpoint == 'E1':
        low, high = result['ci95']
        result['equivalence_5pp'] = ('not_assessable_degenerate_bootstrap' if result['bootstrap_degenerate'] else
                                    'inside_margin' if low > -.05 and high < .05 else 'inconclusive_or_outside_margin')
    if endpoint == 'E2':
        rates = [sum(v[index] for v in admissibility)/len(admissibility) for index in [0, 1]]
        result['admissibility_before_after'] = rates
        result['transitions_before_to_after'] = dict(sorted(transitions.items()))
        if min(rates) < .5:
            result.update(inference_status='inconclusive_below50percent_admissibility', p_for_holm=1.)
    return result


def summaries(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row['item_type'], row['layout'], row['filler'])].append(row)
    result = []
    for (typ, layout, filler), selected in sorted(groups.items()):
        n = len(selected)
        result.append({'item_type':typ, 'layout':layout, 'filler':filler, 'n':n,
                       'admissible':sum(r['admissible_commitment'] for r in selected),
                       'latent_reference_match':sum(r['latent_state_match'] for r in selected),
                       'latent_reference_interpretation':'not a correctness/error measure for ambiguous A-uncued' if typ == 'A' and layout == 'uncued' else 'unique-state correctness',
                       'right':sum(r['right_commitment'] for r in selected),
                       'left':sum(r['left_commitment'] for r in selected),
                       'strict_json':sum(r['json_parsed'] and not r['wrapped'] for r in selected),
                       'wrapped':sum(r['wrapped'] for r in selected),
                       'categories':dict(sorted(Counter(r['category'] for r in selected).items())),
                       'day_vector_correct':None if typ == 'A' and layout == 'uncued' else sum(r['junction_slots_match'] for r in selected),
                       'other_slots_correct':None if typ == 'A' and layout == 'uncued' else sum(r['other_slots_match'] for r in selected)})
    return result


def override(rows, depths):
    cells = identity([r for r in rows if r['depth'] in depths])
    result = []
    for typ, layout in [('R','uncued'), ('A','cued')]:
        comparisons = []
        for pair in sorted({key[0] for key in cells}):
            baseline = cells[(pair,typ,layout,'none')]
            # This alignment is a predeclared cue-direction hypothesis, not an
            # assertion about how humans or these models actually read pauses.
            filler = 'before' if baseline['attachment'] == 0 else 'after'
            shifted = cells[(pair,typ,layout,filler)]
            comparisons.append((int(not shifted['admissible_commitment'])-int(not baseline['admissible_commitment']),
                                int(shifted['category']=='L2_outside_readings')-int(baseline['category']=='L2_outside_readings'),
                                int(shifted['schema_valid'] and shifted['other_slots_match'] and not shifted['junction_slots_match'])-
                                int(baseline['schema_valid'] and baseline['other_slots_match'] and not baseline['junction_slots_match'])))
        result.append({'item_type':typ,'layout':layout,'pairs':len(comparisons),
                       'hypothesized_misleading_cue_minus_none':sum(c[0] for c in comparisons)/len(comparisons),
                       'L2_only_difference':sum(c[1] for c in comparisons)/len(comparisons),
                       'day_vector_error_with_other_slots_correct_difference':sum(c[2] for c in comparisons)/len(comparisons),
                       'scope':'descriptive; day-vector error is not proof of an internal attachment mechanism'})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    selection = json.loads((ROOT/'analysis/main_selection.json').read_text())
    input_path = ROOT/'pivot/inputs/main.jsonl'
    if hashlib.sha256(input_path.read_bytes()).hexdigest() != selection['selected_input_sha256']:
        raise SystemExit('Selected/frozen main input changed')
    inputs = {r['row_id']:r for r in map(json.loads,input_path.read_text().splitlines())}
    models = json.loads((ROOT/'pivot/configs/models.json').read_text())
    expected = {(model['id'],row_id,pid) for model in models for row_id in inputs for pid in [0,1]}
    raw = [json.loads(line) for path in args.raw.glob('*.jsonl') for line in path.read_text().splitlines()]
    keys = [(r['model_id'],r['row_id'],r['prompt_id']) for r in raw]
    if len(keys) != len(expected) or set(keys) != expected:
        raise SystemExit('Incomplete/duplicate main results, not a completed experiment')
    receipt = json.loads((args.raw/'experiment_receipt.json').read_text())
    if receipt['phase'] != 'main' or not receipt['completed'] or not receipt['complete_keyset'] or receipt['commit'] != args.commit or receipt['input_sha256'] != selection['selected_input_sha256'] or not receipt.get('structured_decoding') or receipt.get('structured_backend')!='xgrammar' or receipt.get('structured_disable_any_whitespace') is not True:
        raise SystemExit('Main receipt/provenance mismatch')
    if not engine_receipt_valid(receipt):
        raise SystemExit('Main structured-engine/spacing receipt missing or wrong')
    revisions = {m['id']:m['revision'] for m in models}
    scored = []
    for output in raw:
        row = inputs[output['row_id']]
        if (not output.get('structured_decoding') or output.get('structured_backend')!='xgrammar' or output.get('structured_disable_any_whitespace') is not True or
                output.get('schema_sha256')!=hashlib.sha256((ROOT/'pivot/configs'/f"{row['family']}-state.json").read_bytes()).hexdigest()):
            raise SystemExit('Main structured constraint provenance mismatch')
        parsed, wrapped = parse(output['text'])
        lexical, reference = fixed_contract_checks(output['text'], parsed, row['family'])
        if not lexical or not reference or lexical != reference or output.get('fixed_separator_lexer_valid') is not True or output.get('fixed_separator_reference_valid') is not True:
            raise SystemExit('Fixed separator checks disagree/fail; raw retained, no rescue')
        if parsed is None or wrapped or not validator(row['family'],'state').is_valid(parsed):
            raise SystemExit('Raw structured constraint violated; no canonicalization rescue')
        if output['commit'] != args.commit or output['run_id'] != receipt['run_id'] or output['revision'] != revisions[output['model_id']] or output['finish_reason'] == 'length':
            raise SystemExit('Main raw source/model/run/truncation mismatch')
        if any(output[k] != row[k] for k in ['base_id','pair_id','family','split','item_type','depth','style','layout','filler']):
            raise SystemExit('Main raw/input metadata mismatch')
        scored.append({k:row[k] for k in ['row_id','base_id','pair_id','template_id','family','depth','style','item_type','layout','filler','attachment']} |
                      {'model_id':output['model_id'],'prompt_id':output['prompt_id'],'run_id':output['run_id'],'commit':output['commit']} |
                      score(output['text'],row))
    report = {'phase':'independent main','run_id':receipt['run_id'],'source_commit':args.commit,
              'selected_input_sha256':selection['selected_input_sha256'],'outputs':len(scored),
              'complete_keyset':True,'models':[],'primary_family_size':4,
              'analysis':'frozen centered hierarchical bootstrap10000/addone; Holm4; constant-bootstrap results descriptive only',
              'human_annotation':'not_performed','ASR':'not_measured','statistical_scope':'controlled grammar,24surface frames maximum'}
    primary_refs = []
    for model in models:
        name = model['id']
        all_rows = [r for r in scored if r['model_id']==name]
        depths = selection['eligible_depths_by_model'][name]
        result = {'model_id':name,'eligible_depths':depths,'primary':{},'preambleB_sensitivity':{},'cells_all_selected_depths':{},'cells_confirmatory_depths':{}}
        for pid in [0,1]:
            rows = [r for r in all_rows if r['prompt_id']==pid]
            result['cells_all_selected_depths'][str(pid)] = summaries(rows)
            if depths:
                subset = [r for r in rows if r['depth'] in depths]
                result['cells_confirmatory_depths'][str(pid)] = summaries(subset)
                result.setdefault('override_descriptive',{})[str(pid)] = override(rows,depths)
            for endpoint in ['E1','E2']:
                value = primary(rows,depths,endpoint,bool(depths) and (endpoint=='E1' or selection['e2_calibration_entry_by_model'][name]))
                destination = result['primary'] if pid==0 else result['preambleB_sensitivity']
                destination[endpoint] = value
                if pid==0:
                    primary_refs.append(value)
        report['models'].append(result)
    adjusted = holm_four([r['p_for_holm'] for r in primary_refs])
    for value, p in zip(primary_refs,adjusted):
        value['p_holm_four'] = p
        value['reject_zero_at_05'] = p < .05 and value.get('inference_status')=='approximate_empirical_bootstrap'
    common = sorted(set.intersection(*(set(r['eligible_depths']) for r in report['models'])))
    report['common_depths'] = common
    report['common_depth_sensitivity'] = []
    if common:
        for model in models:
            rows = [r for r in scored if r['model_id']==model['id'] and r['prompt_id']==0]
            report['common_depth_sensitivity'].append({'model_id':model['id'],'depths':common,
                                                       'E1':primary(rows,common,'E1',True),'E2':primary(rows,common,'E2',selection['e2_calibration_entry_by_model'][model['id']])})
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit('Refuse overwrite of previous result analysis')
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'scored.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in scored))
    (args.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'outputs':len(scored),'run_id':report['run_id'],'models':[{'model_id':m['model_id'],'depths':m['eligible_depths'],'primary':m['primary']} for m in report['models']]}))


if __name__ == '__main__':
    main()

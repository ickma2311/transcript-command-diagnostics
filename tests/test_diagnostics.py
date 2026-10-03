"""Verify ambiguity accounting and input-identity protections in the public interface."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from score_predictions import evaluate

class DiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rows=[json.loads(x) for x in (ROOT/'pivot/inputs/main.jsonl').read_text().splitlines()]
        cls.ambiguous=next(r for r in rows if r['item_type']=='A' and r['layout']=='uncued' and r['filler']=='none')
        cls.unique=next(r for r in rows if r['item_type']=='R' and r['layout']=='uncued' and r['filler']=='none')

    def test_licensed_alternate_not_counted_as_unique_state_error(self):
        row=self.ambiguous
        alternate=next(x for x in row['readings'] if x!=row['gold'])
        result=evaluate([row],[{'row_id':row['row_id'],'text':json.dumps(alternate)}])
        self.assertEqual(result['scored'][0]['category'],'L3_licensed_alternate')
        self.assertEqual(result['groups'][0]['grammar_admissible'],1)
        self.assertEqual(result['groups'][0]['reference_matches'],0)
        self.assertIsNone(result['groups'][0]['unique_state_accuracy'])

    def test_wrong_prohibition_is_outside_readings(self):
        row=self.unique;bad=copy.deepcopy(row['gold']);bad['prohibited'][0]['object']='wrongobject'
        result=evaluate([row],[{'row_id':row['row_id'],'text':json.dumps(bad)}])
        self.assertEqual(result['scored'][0]['category'],'L2_outside_readings')
        self.assertEqual(result['groups'][0]['unique_state_accuracy'],0)

    def test_duplicate_or_unknown_identity_rejected(self):
        row=self.unique;pred={'row_id':row['row_id'],'text':json.dumps(row['gold'])}
        with self.assertRaises(ValueError):evaluate([row],[pred,pred])
        with self.assertRaises(ValueError):evaluate([row],[dict(pred,row_id='unknown')])

    def test_unique_state_reference_is_correctness(self):
        row=self.unique;result=evaluate([row],[{'row_id':row['row_id'],'text':json.dumps(row['gold'])}])
        self.assertEqual(result['groups'][0]['unique_state_accuracy'],1)
        self.assertTrue(result['scored'][0]['reference_agreement_is_correctness'])

if __name__=='__main__':unittest.main()

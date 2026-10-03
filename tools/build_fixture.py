"""Run a copy of the original generator in a new external directory."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output.resolve()
    if out.exists() or out==ROOT or ROOT in out.parents:raise SystemExit('Output must be a new directory outside this checkout')
    (out/'pivot').mkdir(parents=True);(out/'protocol').mkdir()
    (out/'pivot/inputs').mkdir()
    for name in ['build.py','regex_parser.py','earley_parser.py','scoring.py']:
        shutil.copy2(ROOT/'pivot'/name,out/'pivot'/name)
    shutil.copytree(ROOT/'pivot/configs',out/'pivot/configs')
    result=subprocess.run([sys.executable,str(out/'pivot/build.py')],check=False,timeout=45,capture_output=True,text=True)
    if result.returncode:raise SystemExit(result.stderr or result.stdout)
    print(json.dumps({'output':str(out),'generator_result':json.loads(result.stdout),'model_inference':False}))

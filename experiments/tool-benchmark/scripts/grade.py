"""Execute acceptance checks outside the agent workspace and emit JSON scores."""
import argparse
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import unittest

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('task',choices=['T1','T2','T3']);parser.add_argument('workspace',type=Path)
args=parser.parse_args();workspace=args.workspace.resolve();os.chdir(workspace);sys.path.insert(0,str(workspace))
spec=importlib.util.spec_from_file_location('acceptance',root/'acceptance'/f'{args.task}.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
stream=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromModule(module)
result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
baseline=root/'fixture/tests/test_existing.py';current=workspace/'tests/test_existing.py'
unchanged=current.exists() and current.read_bytes()==baseline.read_bytes()
failed_cases={getattr(test,'test_case',test).id() for test,_ in result.failures+result.errors}
print(json.dumps({'task':args.task,'testsRun':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
                 'passed':result.testsRun-len(failed_cases),'existingTestsUnchanged':unchanged,
                 'success':result.wasSuccessful() and unchanged,'output':stream.getvalue()}))
sys.exit(0 if result.wasSuccessful() and unchanged else 1)

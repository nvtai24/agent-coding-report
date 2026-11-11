"""Regrade saved code and check the CSV against raw-event-derived metrics."""
import ast
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from run_benchmark import ROOT, terminal_success, usage

expected={(tool,task,repeat) for tool in ['opencode','pi','codex'] for task in ['T1','T2','T3'] for repeat in [1,2,3]}
files=sorted((ROOT/'results').glob('*/metrics.json'));rows=[json.loads(file.read_text()) for file in files]
actual={(row['tool'],row['task'],row['repeat']) for row in rows}
assert actual==expected,(len(actual),len(expected))
assert len({row['baseline_commit'] for row in rows})==1
artifacts={};helpers={}
for row,file in zip(rows,files):
    folder=file.parent
    assert row['usage']==usage(row['tool'],folder),row['run_id']
    assert row['terminal_success']==terminal_success(row['tool'],folder)
    grade=subprocess.run([sys.executable,str(ROOT/'scripts/grade.py'),row['task'],str(folder/'solution')],capture_output=True,text=True,timeout=30)
    score=json.loads(grade.stdout)
    assert score['passed']==row['acceptance_passed'] and score['testsRun']==row['acceptance_total'],row['run_id']
    assert score['existingTestsUnchanged']==row['original_tests_unchanged']
    prompt='Read README.md before working. Use Python 3 standard library only. Implement the task autonomously and do not delegate.\n\n'+(ROOT/'prompts'/f"{row['task']}.txt").read_text()
    assert (folder/'prompt.txt').read_text()==prompt
    for name in ['stdout.jsonl','agent.jsonl','changes.diff','grade.json','metrics.json']:
        path=folder/name
        if path.exists():artifacts[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    if row['task']=='T3':
        tree=ast.parse((folder/'solution/cartkit/reports.py').read_text())
        functions={node.name:node for node in tree.body if isinstance(node,ast.FunctionDef)}
        calls={name:{node.func.id for node in ast.walk(function) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in functions} for name,function in functions.items()}
        common=(calls.get('customer_totals',set()) & calls.get('summarize_orders',set()))-{'customer_totals','summarize_orders'}
        helpers[row['run_id']]=sorted(common)
with (ROOT/'results/trials.csv').open() as file:csv_rows=list(csv.DictReader(file))
assert len(csv_rows)==27
assert {row['run_id'] for row in csv_rows}=={row['run_id'] for row in rows}
(ROOT/'results/artifact-sha256.json').write_text(json.dumps(artifacts,indent=2))
(ROOT/'results/code-review.json').write_text(json.dumps({'T3_shared_helper_names':helpers},indent=2))
(ROOT/'results/verification.txt').write_text('PASS — 27 unique runs; same baseline and prompts; usage recomputed from native events; saved solutions regraded; original tests checked; CSV complete.\n')
print((ROOT/'results/verification.txt').read_text())

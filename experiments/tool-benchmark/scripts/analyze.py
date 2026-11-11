"""Normalize, validate and aggregate the captured native event streams."""
import csv
import hashlib
import json
from pathlib import Path
import platform
import statistics
from run_benchmark import ROOT, terminal_success, usage

TOOLS=['opencode','pi','codex']


def describe(values):
    return {'median':statistics.median(values),'min':min(values),'max':max(values),'mean':statistics.mean(values),'sum':sum(values)}


rows=[]
for file in sorted((ROOT/'results').glob('*/metrics.json')):
    row=json.loads(file.read_text());folder=file.parent
    row['terminal_success']=terminal_success(row['tool'],folder)
    row['usage']=usage(row['tool'],folder)
    score=json.loads((folder/'grade.json').read_text())
    row['success']=row['exit_code']==0 and not row['timed_out'] and row['terminal_success'] and score['success'] and row['existing_tests_pass']
    assert row['usage']['input_total']==sum(row['usage'][key] for key in ['input_uncached','input_cached','input_cache_write'])
    assert row['usage']['output_total']>=row['usage']['reasoning']>=0
    if row['terminal_success']:assert row['usage']['usage_available'],row['run_id']
    file.write_text(json.dumps(row,ensure_ascii=False,indent=2));rows.append(row)

summary={'model':'gpt-6.1-sol','reasoning':'medium','planned':27,'completed':len(rows),'tools':{},'by_task':{}}
for tool in TOOLS:
    selected=[row for row in rows if row['tool']==tool]
    if not selected:continue
    successes=sum(row['success'] for row in selected)
    aggregate={'attempts':len(selected),'successes':successes,'completion_rate':successes/len(selected),
               'seconds':describe([r['elapsed_seconds'] for r in selected]),'tokens':describe([r['usage']['total_tokens'] for r in selected]),
               'input_total':sum(r['usage']['input_total'] for r in selected),'input_cached':sum(r['usage']['input_cached'] for r in selected),
               'input_uncached':sum(r['usage']['input_uncached'] for r in selected),'output_total':sum(r['usage']['output_total'] for r in selected),
               'reasoning':sum(r['usage']['reasoning'] for r in selected),'acceptance_passed':sum(r['acceptance_passed'] for r in selected),
               'acceptance_total':sum(r['acceptance_total'] for r in selected)}
    summary['tools'][tool]=aggregate
    for task in ['T1','T2','T3']:
        subset=[r for r in selected if r['task']==task]
        if subset:summary['by_task'].setdefault(task,{})[tool]={'attempts':len(subset),'successes':sum(r['success'] for r in subset),
            'seconds':describe([r['elapsed_seconds'] for r in subset]),'tokens':describe([r['usage']['total_tokens'] for r in subset])}

(ROOT/'results/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
fields=['run_id','tool','task','repeat','success','terminal_success','elapsed_seconds','acceptance_passed','acceptance_total','existing_tests_pass','original_tests_unchanged','exit_code','timed_out','input_total','input_uncached','input_cached','input_cache_write','output_total','reasoning','total_tokens','model_calls','tool_calls']
with (ROOT/'results/trials.csv').open('w',newline='') as file:
    writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader()
    for row in rows:writer.writerow({key:row.get(key,row['usage'].get(key)) for key in fields})

manifest={'python':platform.python_version(),'platform':platform.platform(),'model':'gpt-6.1-sol','reasoning':'medium',
          'versions':{'opencode':'2.2.7','pi':'1.5.0','codex':'0.166.0-alpha.6','bun':'1.4.4'},
          'baseline_commits':sorted({r['baseline_commit'] for r in rows}),
          'task_prompt_sha256':{task:hashlib.sha256((ROOT/'prompts'/f'{task}.txt').read_bytes()).hexdigest() for task in ['T1','T2','T3']}}
(ROOT/'results/manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({tool:{key:value[key] for key in ['attempts','successes','completion_rate']} for tool,value in summary['tools'].items()}))

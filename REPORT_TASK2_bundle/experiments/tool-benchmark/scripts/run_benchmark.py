"""Run identical independent tasks through native OpenCode, Pi and Codex entry points."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from server import BASE, ROOT, server

BUN='/tmp/opencode-lab/runtime/bun-linux-x64/bun'
CODEX=os.getenv('BENCH_CODEX_BIN') or shutil.which('codex') or '/usr/lib/chatgpt/resources/codex'
PI=ROOT/'node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js'
TOOLS=['opencode','pi','codex']


def command_output(command,cwd):
    return subprocess.run(command,cwd=cwd,capture_output=True,text=True,check=True).stdout


def prepare(task,run_id):
    workspace=BASE/'workspaces'/run_id
    if workspace.exists():raise RuntimeError(f'Refusing to reuse workspace {workspace}')
    shutil.copytree(ROOT/'fixture',workspace,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for command in [['git','init','-q'],['git','add','.'],['git','-c','user.name=Benchmark','-c','user.email=benchmark@example.invalid','commit','-qm','Fixed benchmark input']]:
        subprocess.run(command,cwd=workspace,check=True,env={**os.environ,'GIT_AUTHOR_DATE':'2026-11-11T00:00:00+00:00','GIT_COMMITTER_DATE':'2026-11-11T00:00:00+00:00'})
    return workspace


def launch(command,workspace,env,output,timeout):
    start=time.perf_counter();timed_out=False
    with (output/'stdout.jsonl').open('w') as stdout,(output/'stderr.log').open('w') as stderr:
        process=subprocess.Popen(command,cwd=workspace,env=env,stdout=stdout,stderr=stderr,stdin=subprocess.DEVNULL,start_new_session=True)
        try:code=process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True;os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            code=124
    return code,timed_out,round(time.perf_counter()-start,3)


def events(path):
    rows=[]
    if not path.exists():return rows
    for line in path.read_text().splitlines():
        try:rows.append(json.loads(line))
        except json.JSONDecodeError:pass
    return rows


def usage(tool,output):
    rows=events(output/('agent.jsonl' if tool=='opencode' else 'stdout.jsonl'))
    totals={'input_total':0,'input_uncached':0,'input_cached':0,'input_cache_write':0,'output_total':0,'reasoning':0,'model_calls':0,'tool_calls':0}
    for event in rows:
        if tool=='opencode':
            if event['type']=='session.tool.called':totals['tool_calls']+=1
            if event['type']!='session.step.ended':continue
            data=event['data']['tokens'];cache=data.get('cache',{})
            uncached=data.get('input',0);cached=cache.get('read',0);written=cache.get('write',0)
            output_tokens=data.get('output',0)+data.get('reasoning',0);reasoning=data.get('reasoning',0)
        elif tool=='pi':
            if event['type']=='tool_execution_start':totals['tool_calls']+=1
            message=event.get('message',{})
            if event['type']!='message_end' or message.get('role')!='assistant':continue
            data=message.get('usage',{})
            uncached=data.get('input',0);cached=data.get('cacheRead',0);written=data.get('cacheWrite',0)
            output_tokens=data.get('output',0);reasoning=data.get('reasoning',0)
        else:
            if event['type']=='item.completed' and event.get('item',{}).get('type') in ['command_execution','file_change']:totals['tool_calls']+=1
            if event['type']!='turn.completed':continue
            data=event['usage'];cached=data.get('cached_input_tokens',0);written=data.get('cache_write_input_tokens',0)
            uncached=data['input_tokens']-cached-written;output_tokens=data['output_tokens'];reasoning=data.get('reasoning_output_tokens',0)
        totals['input_uncached']+=uncached;totals['input_cached']+=cached;totals['input_cache_write']+=written
        totals['input_total']+=uncached+cached+written;totals['output_total']+=output_tokens;totals['reasoning']+=reasoning
        totals['model_calls']+=1
    if tool=='codex':totals['model_calls']=None  # turn.completed reports aggregate usage, not individual calls.
    totals['total_tokens']=totals['input_total']+totals['output_total']
    totals['usage_available']=totals['total_tokens']>0
    return totals



def terminal_success(tool,output):
    rows=events(output/('agent.jsonl' if tool=='opencode' else 'stdout.jsonl'))
    if tool=='opencode':
        terminal=[e['type'] for e in rows if e['type'].startswith('session.execution.') and e['type']!='session.execution.started']
        return bool(terminal) and terminal[-1]=='session.execution.succeeded'
    if tool=='pi':
        settled=[e for e in rows if e['type']=='agent_settled']
        messages=[e['message'] for e in rows if e['type']=='message_end' and e.get('message',{}).get('role')=='assistant']
        return bool(settled and messages) and not settled[-1].get('aborted') and messages[-1].get('stopReason') not in ['error','aborted','length']
    terminal=[e['type'] for e in rows if e['type'] in ['turn.completed','turn.failed']]
    return bool(terminal) and terminal[-1]=='turn.completed'


def grade(task,workspace,output):
    expected=json.loads((ROOT/'dataset.json').read_text())['tasks'][task]['testCount']
    try:
        acceptance=subprocess.run([sys.executable,str(ROOT/'scripts/grade.py'),task,str(workspace)],capture_output=True,text=True,timeout=30)
        try:score=json.loads(acceptance.stdout)
        except json.JSONDecodeError:
            original=workspace/'tests/test_existing.py'
            score={'task':task,'testsRun':expected,'passed':0,'failures':0,'errors':1,'success':False,
                   'existingTestsUnchanged':original.exists() and original.read_bytes()==(ROOT/'fixture/tests/test_existing.py').read_bytes(),
                   'output':acceptance.stdout+acceptance.stderr}
    except subprocess.TimeoutExpired:
        score={'task':task,'testsRun':expected,'passed':0,'failures':0,'errors':1,'success':False,'existingTestsUnchanged':False,'output':'Acceptance evaluator exceeded 30 seconds.'}
    (output/'grade.json').write_text(json.dumps(score,indent=2))
    try:
        existing=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=workspace,capture_output=True,text=True,timeout=30)
        (output/'tests.log').write_text(existing.stdout+existing.stderr)
        test_code=existing.returncode
    except subprocess.TimeoutExpired:
        (output/'tests.log').write_text('Repository tests exceeded 30 seconds.')
        test_code=124
    return score,test_code


def run(tool,task,repeat,timeout):
    run_id=f'{tool}-{task}-r{repeat}';output=ROOT/'results'/run_id
    if (output/'metrics.json').exists():
        print('SKIP completed',run_id,flush=True);return
    output.mkdir(parents=True,exist_ok=True);workspace=prepare(task,run_id)
    env=os.environ.copy();env['PATH']=str(Path(BUN).parent)+':'+env.get('PATH','')
    env['CODEX_HOME']=str(BASE/'codex-home');env['PI_CODING_AGENT_DIR']=str(BASE/'pi-agent')
    prompt='Read README.md before working. Use Python 3 standard library only. Implement the task autonomously and do not delegate.\n\n'+(ROOT/'prompts'/f'{task}.txt').read_text()
    (output/'prompt.txt').write_text(prompt)
    if tool=='opencode':
        command=[BUN,str(ROOT/'scripts/run-opencode.ts'),str(workspace),str(output/'prompt.txt'),str(output/'agent')]
    elif tool=='pi':
        command=[BUN,str(PI),'--mode','json','--no-session','--no-extensions','--no-skills','--provider','openai-codex','--model','gpt-6.1-sol','--thinking','medium',prompt]
    else:
        command=[CODEX,'-a','never','exec','--json','--ephemeral','--sandbox','workspace-write','-m','gpt-6.1-sol',
                 '-c','model_reasoning_effort="medium"','-c','features.multi_agent=false',prompt]
    started=datetime.now(timezone.utc).isoformat();code,timed_out,elapsed=launch(command,workspace,env,output,timeout)
    score,test_code=grade(task,workspace,output)
    subprocess.run(['git','add','-N','.'],cwd=workspace,check=True)
    diff=command_output(['git','diff','--no-ext-diff','HEAD'],workspace);(output/'changes.diff').write_text(diff)
    changed=command_output(['git','diff','--name-only','HEAD'],workspace).splitlines()
    shutil.copytree(workspace,output/'solution',ignore=shutil.ignore_patterns('.git','__pycache__','*.pyc'))
    metrics={'run_id':run_id,'tool':tool,'task':task,'repeat':repeat,'model':'gpt-6.1-sol','reasoning_effort':'medium',
             'started_at':started,'elapsed_seconds':elapsed,'exit_code':code,'timed_out':timed_out,
             'workspace':str(workspace),'baseline_commit':command_output(['git','rev-parse','HEAD'],workspace).strip(),
             'acceptance_passed':score['passed'],'acceptance_total':score['testsRun'],
             'existing_tests_pass':test_code==0,'original_tests_unchanged':score['existingTestsUnchanged'],
             'terminal_success':terminal_success(tool,output),
             'success':code==0 and not timed_out and terminal_success(tool,output) and score['success'] and test_code==0,'changed_files':changed,
             'usage':usage(tool,output),'command':command[:-1] if tool!='opencode' else command}
    (output/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2))
    print(json.dumps({key:metrics[key] for key in ['run_id','success','elapsed_seconds','acceptance_passed','acceptance_total']})[:-1]+',"tokens":'+str(metrics['usage']['total_tokens'])+'}',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--rounds',type=int,default=3);parser.add_argument('--timeout',type=int,default=240);parser.add_argument('--pilot',action='store_true')
    args=parser.parse_args();BASE.mkdir(exist_ok=True)
    # A Latin-square rotation gives each tool first, middle and last position over three repeats.
    schedule=[]
    for repeat in range(1,args.rounds+1):
        for task_index,task in enumerate(['T1','T2','T3']):
            offset=(repeat-1+task_index)%len(TOOLS)
            for tool in TOOLS[offset:]+TOOLS[:offset]:schedule.append((tool,task,repeat))
    if args.pilot:schedule=[(tool,'T1',1) for tool in TOOLS]
    (ROOT/'results/schedule.json').write_text(json.dumps(schedule,indent=2))
    with server():
        for tool,task,repeat in schedule:run(tool,task,repeat,args.timeout)

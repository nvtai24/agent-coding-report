import os
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[1];base=Path('/tmp/coding-benchmark')
project=base/'smoke';project.mkdir(exist_ok=True)
env=os.environ.copy();env['CODEX_HOME']=str(base/'codex-home');env['PI_CODING_AGENT_DIR']=str(base/'pi-agent')
env['PATH']='/tmp/opencode-lab/runtime/bun-linux-x64:'+env.get('PATH','')
commands={
 'codex':['/usr/lib/chatgpt/resources/codex','-a','never','exec','--json','--ephemeral','--sandbox','workspace-write','-m','gpt-6.1-sol','-c','model_reasoning_effort="medium"','Reply exactly BENCHMARK_READY. Do not call tools.'],
 'pi':['/tmp/opencode-lab/runtime/bun-linux-x64/bun',str(root/'node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js'),'--mode','json','--no-session','--no-extensions','--no-skills','--provider','openai-codex','--model','gpt-6.1-sol','--thinking','medium','Reply exactly BENCHMARK_READY. Do not call tools.'],
}
for name,command in commands.items():
 with (root/'results'/f'smoke-native-{name}.jsonl').open('w') as out,(root/'results'/f'smoke-native-{name}.stderr').open('w') as err:
  try:result=subprocess.run(command,cwd=project,env=env,stdout=out,stderr=err,timeout=90);code=result.returncode
  except subprocess.TimeoutExpired:code=124
 print(name,'exit',code)

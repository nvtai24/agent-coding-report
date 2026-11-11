import os
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[1]
project=Path('/tmp/coding-benchmark/smoke');project.mkdir(parents=True,exist_ok=True)
subprocess.run(['git','init','-q',str(project)],check=True)
env=os.environ.copy()
env['CODEX_HOME']='/tmp/coding-benchmark/codex-home'
Path(env['CODEX_HOME']).mkdir(parents=True,exist_ok=True)
env['BENCH_OPENCODE_KEY']='public'
command=['/usr/lib/chatgpt/resources/codex','-a','never','exec','--json','--ephemeral',
 '--sandbox','workspace-write','-C',str(project),'-m','minimax-m3.1-flash-free',
 '-c','model_provider="benchmark"',
 '-c','model_providers.benchmark.name="OpenCode public model"',
 '-c','model_providers.benchmark.base_url="https://opencode.ai/inference/openai/v1"',
 '-c','model_providers.benchmark.env_key="BENCH_OPENCODE_KEY"',
 '-c','model_providers.benchmark.wire_api="responses"',
 '-c','model_providers.benchmark.requires_openai_auth=false',
 '-c','model_providers.benchmark.supports_websockets=false',
 'Reply exactly BENCHMARK_READY. Do not call tools.']
try:
 result=subprocess.run(command,env=env,text=True,capture_output=True,timeout=90)
except subprocess.TimeoutExpired as error:
 (root/'results/smoke-codex.jsonl').write_bytes(error.stdout or b'')
 (root/'results/smoke-codex.stderr').write_bytes(error.stderr or b'')
 raise
(root/'results/smoke-codex.jsonl').write_text(result.stdout)
(root/'results/smoke-codex.stderr').write_text(result.stderr)
print(result.stdout[-4000:]);print(result.stderr[-1500:]);print('exit',result.returncode)

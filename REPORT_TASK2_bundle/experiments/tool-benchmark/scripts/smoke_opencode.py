from pathlib import Path
import subprocess
from server import BASE, ROOT, server

prompt=BASE/'smoke-prompt.txt';prompt.write_text('Reply exactly BENCHMARK_READY. Do not call tools.')
with server():
    result=subprocess.run(['/tmp/opencode-lab/runtime/bun-linux-x64/bun','scripts/run-opencode.ts',str(BASE/'smoke'),str(prompt),str(ROOT/'results/smoke-native-opencode')],cwd=ROOT,timeout=240)
    print('exit',result.returncode)

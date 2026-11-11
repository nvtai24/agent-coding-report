"""Start an isolated OpenCode server and import only its existing OpenAI credential."""
import base64
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/tmp/coding-benchmark')
URL='http://127.0.0.1:14427'
BASIC='Basic '+base64.b64encode(b'opencode:benchmark-local').decode()


def api(path,body=None):
    request=urllib.request.Request(URL+path,headers={'Authorization':BASIC,'Content-Type':'application/json'},
        data=None if body is None else json.dumps(body).encode())
    with urllib.request.urlopen(request,timeout=60) as response:
        return json.loads(response.read())


@contextmanager
def server():
    env=os.environ.copy();home=BASE/'opencode-home'
    for key,folder in [('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache'),('XDG_STATE_HOME','state')]:
        location=home/folder;location.mkdir(parents=True,exist_ok=True);env[key]=str(location)
    env['OPENCODE_TEST_HOME']=str(home);env['OPENCODE_PASSWORD']='benchmark-local'
    env['PATH']='/tmp/opencode-lab/runtime/bun-linux-x64:'+env.get('PATH','')
    config=home/'config/opencode';config.mkdir(exist_ok=True)
    (config/'opencode.json').write_text(json.dumps({'model':'openai/gpt-6.1-sol','permissions':[{'action':'*','resource':'*','effect':'allow'}]}))
    cwd=BASE/'smoke';cwd.mkdir(parents=True,exist_ok=True)
    log=(ROOT/'results/opencode-server.log').open('a')
    process=subprocess.Popen(['/tmp/opencode-lab/v2/package/bin/opencode','serve','--hostname','127.0.0.1','--port','14427'],env=env,cwd=cwd,stdout=log,stderr=log)
    try:
        for attempt in range(120):
            if process.poll() is not None:raise RuntimeError('OpenCode server exited; inspect server log')
            try:api('/api/info');break
            except Exception:time.sleep(.25)
        else:raise RuntimeError('OpenCode server startup timeout')
        source=Path(os.getenv('BENCH_OPENCODE_DB',str(Path.home()/'.local/share/opencode/opencode.db')))
        connection=sqlite3.connect(f'file:{source}?mode=ro',uri=True)
        row=connection.execute("SELECT value FROM credential WHERE integration_id='openai' AND active=1 LIMIT 1").fetchone();connection.close()
        if not row:raise RuntimeError('OpenCode has no active OpenAI credential')
        api('/api/credential',{'integrationID':'openai','label':'Benchmark private auth','value':json.loads(row[0]),'activate':True})
        yield
    finally:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait()
        log.close()

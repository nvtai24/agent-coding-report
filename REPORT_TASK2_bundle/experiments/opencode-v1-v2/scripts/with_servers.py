"""Run a command while both isolated lab servers are alive."""
import json
import subprocess
import sys
import time
import urllib.request
from lab_env import LAB, ROOT, binary, environment

processes=[]
try:
    for version, port in [(1, 14195), (2, 14227)]:
        env=environment(version)
        env['OPENCODE_PASSWORD']='lab-local-only'
        env['OPENCODE_SERVER_PASSWORD']='lab-local-only'
        log=(ROOT/'evidence'/f'server-v{version}.log').open('a')
        process=subprocess.Popen([binary(version),'serve','--hostname','127.0.0.1','--port',str(port), '--print-logs', '--log-level', 'DEBUG' if version == 1 else 'debug'],
            cwd=LAB/f'project-v{version}',env=env,stdout=log,stderr=log)
        processes.append((process,log))
    for port,path in [(14195,'/global/health'),(14227,'/api/info')]:
        for attempt in range(120):
            if processes[0][0].poll() is not None or processes[1][0].poll() is not None:
                raise RuntimeError('A lab server exited before readiness. See evidence/server-v*.log')
            try:
                req=urllib.request.Request(f'http://127.0.0.1:{port}{path}',headers={'Authorization':'Basic b3BlbmNvZGU6bGFiLWxvY2FsLW9ubHk='})
                with urllib.request.urlopen(req,timeout=2) as response:
                    response.read()
                break
            except Exception:
                time.sleep(.5)
        else:
            raise RuntimeError(f'Server {port} did not become ready')
    result=subprocess.run(sys.argv[1:],cwd=ROOT,env=environment(2))
    sys.exit(result.returncode)
finally:
    for process,log in processes:
        process.terminate()
    for process,log in processes:
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        log.close()

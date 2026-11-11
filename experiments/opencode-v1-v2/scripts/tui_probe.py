"""Open a real TUI against the lab service through a pseudo terminal."""
import fcntl
import json
import os
import pty
import re
import select
import struct
import subprocess
import sys
import termios
import time
from pathlib import Path

master,slave=pty.openpty()
fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',40,120,0,0))
command=['/tmp/opencode-lab/v2/package/bin/opencode','--server',sys.argv[1],'--session',sys.argv[2],'/tmp/opencode-lab/project-v2']
env=os.environ.copy();env['TERM']='xterm-256color'
process=subprocess.Popen(command,stdin=slave,stdout=slave,stderr=slave,env=env,start_new_session=True)
os.close(slave)
data=bytearray();deadline=time.monotonic()+8
try:
    while time.monotonic()<deadline and process.poll() is None:
        if select.select([master],[],[],.2)[0]:
            try: data.extend(os.read(master,65536))
            except OSError: break
    os.write(master,b'\x03')
    try: process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        os.write(master,b'\x03')
        try: process.wait(timeout=3)
        except subprocess.TimeoutExpired: process.terminate();process.wait(timeout=3)
finally:
    if process.poll() is None:process.kill();process.wait()
    os.close(master)
text=data.decode('utf8','replace')
text=re.sub(r'\x1b\][^\x07]*(?:\x07|\x1b\\)','',text)
text=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',text)
root=Path(__file__).resolve().parents[1]/'evidence'
(root/'tui-render.txt').write_text(text)
print(json.dumps({'exitCode':process.returncode,'bytes':len(data),'expectedTitle':'Shared lab session','titlePrefixVisible':'Shared lab sessio' in text,'connectionError':'ECONNREFUSED' in text}))

"""Prepare private, temporary native credentials. Never write secrets into results."""
import base64
import json
import os
from pathlib import Path
import shutil

base=Path('/tmp/coding-benchmark');base.mkdir(exist_ok=True,mode=0o700);base.chmod(0o700)
codex=base/'codex-home';codex.mkdir(parents=True,exist_ok=True)
source=Path(os.getenv('BENCH_CODEX_AUTH',str(Path.home()/'.codex/auth.json')))
shutil.copyfile(source,codex/'auth.json');(codex/'auth.json').chmod(0o600)
auth=json.loads(source.read_text())['tokens']
payload=json.loads(base64.urlsafe_b64decode(auth['access_token'].split('.')[1]+'==='))
pi=base/'pi-agent';pi.mkdir(exist_ok=True)
credential={'type':'oauth','access':auth['access_token'],'refresh':auth['refresh_token'],
            'expires':payload.get('exp',0)*1000,'accountId':auth['account_id']}
(pi/'auth.json').write_text(json.dumps({'openai-codex':credential}));(pi/'auth.json').chmod(0o600)
config={'providers':{'openai-codex':{'models':[{'id':'gpt-6.1-sol','name':'GPT-6.1 Sol benchmark','api':'openai-codex-responses','reasoning':True,'input':['text'],'contextWindow':200000,'maxTokens':16384}]}}}
(pi/'models.json').write_text(json.dumps(config,indent=2))
(pi/'settings.json').write_text(json.dumps({'defaultProvider':'openai-codex','defaultModel':'gpt-6.1-sol','defaultThinkingLevel':'medium'}))
print('Prepared private native auth under /tmp/coding-benchmark; no credentials written into the repository.')

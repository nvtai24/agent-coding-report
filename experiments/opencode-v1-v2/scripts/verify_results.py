"""Check the report's factual claims against captured runtime evidence."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]/'evidence'
def read(name):return json.loads((root/name).read_text())
def trace(name):return [json.loads(line) for line in (root/name).read_text().splitlines()]

api=read('api-v2-summary.json')
assert api['terminal']['type']=='session.execution.succeeded'
assert any(item.get('text')=='MIGRATION_API_OK' for message in api['context'] for item in message.get('content',[]))
for version in [1,2]:
    cases={item['name']:item for item in read(f'runtime-v{version}-results.json')}
    for name in ['plugin','allow','ask','deny']:assert not cases[name].get('error'),(version,name)
    events=trace(f'v{version}-ask.jsonl')
    assert sum(item['type']=='permission.asked' for item in events)==1
v1=read('runtime-v1-results.json')
plugin=next(row for row in v1 if row['name']=='plugin')
assert any(part.get('state',{}).get('output')=='MIGRATION_PLUGIN:PORT_OK' for message in plugin['messages'] for part in message['parts'])
deny=next(row for row in v1 if row['name']=='deny')
assert any(part.get('tool')=='bash' and part['state']['status']=='error' for message in deny['messages'] for part in message['parts'])
assert not any(item['type']=='session.tool.success' for item in trace('v2-deny.jsonl'))
assert any('MIGRATION_PLUGIN:PORT_OK' in str(item.get('data',{}).get('content')) for item in trace('v2-plugin.jsonl'))
order=read('rule-order.json')
assert [sum(e['type']=='permission.asked' for e in row['events']) for row in order]==[0,1]
compat={row['label']:row for row in read('plugin-compatibility.json')}
assert any(item.get('id')=='lab.echo' and item['state']['status']=='active' for item in compat['ported']['plugins']['data'])
assert any(item['state']['status']=='failed' and 'default definition' in item['state']['error'] for item in compat['legacy']['plugins']['data'])
background=read('background-timing.json')
for name in ['background-shell','background-subagent']:
    assert background[name]['toolReturnAfterMs']<1000
    assert background[name]['firstExecutionEndAfterMs']<5000
    assert background[name]['completionExecutionEndAfterMs']>5000
assert background['v1BackgroundSubagent']['input']['background'] is True
assert background['v1BackgroundSubagent']['toolReturnMs']<1000
service=read('shared-service.json')
assert service['samePID'] and service['sameSession'] and service['stopped']
assert service['web']['status']==200 and 'text/html' in service['web']['contentType']
assert service['tui']['titlePrefixVisible'] and not service['tui']['connectionError']
(root/'verification.txt').write_text('PASS — captured API, permission, rule precedence, background execution, plugin migration and shared-service evidence match report claims.\n')
print((root/'verification.txt').read_text())

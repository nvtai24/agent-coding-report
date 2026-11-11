"""Derive the report's compact observations from raw runtime evidence."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]/'evidence'
summary={}
for version in [1,2]:
    results=json.loads((root/f'runtime-v{version}-results.json').read_text())
    rows=[]
    for result in results:
        events=[json.loads(line) for line in (root/f"v{version}-{result['name']}.jsonl").read_text().splitlines()]
        row={'case':result['name'],'sessionID':result['sessionID'],'elapsedMs':result['elapsedMs'],
             'error':result.get('error'),'permissionAsked':sum(e['type']=='permission.asked' for e in events)}
        if version==2:
            row['tools']=[{'input':e['data'].get('input'),'id':e['data']['id']} for e in events if e['type']=='session.tool.called']
            row['results']=[e['data'] for e in events if e['type'] in ['session.tool.success','session.tool.failed']]
            row['executionFinished']=[e['created'] for e in events if e['type']=='session.execution.succeeded']
        else:
            row['tools']=[part for message in result.get('messages',[]) for part in message['parts'] if part['type']=='tool']
        rows.append(row)
    summary[f'v{version}']=rows
summary['v1ExperimentalBackground']=json.loads((root/'runtime-v1-background-enabled.json').read_text())
summary['ruleOrder']=[{'case':r['name'],'asked':sum(e['type']=='permission.asked' for e in r['events'])} for r in json.loads((root/'rule-order.json').read_text())]
summary['pluginCompatibility']=[{'case':r['label'],'localPlugins':[x for x in r['plugins']['data'] if x.get('source',{}).get('type')=='local']} for r in json.loads((root/'plugin-compatibility.json').read_text())]
(root/'observations.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
for version in ['v1','v2']:
    for r in summary[version]:print(version,r['case'],r['elapsedMs'],r['permissionAsked'],r['error'])

"""Render the benchmark's numerical Markdown tables from the recorded JSON."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
summary=json.loads((root/'results/summary.json').read_text())
rows=[json.loads(path.read_text()) for path in sorted((root/'results').glob('*/metrics.json'))]
labels={'opencode':'OpenCode 2.2.7','pi':'Pi 1.5.0','codex':'Codex CLI 0.166.0-alpha.6'}
tools=list(labels)
def number(value):return f'{value:,.0f}'
def seconds(value):return f'{value:.1f}'

tables={}
lines=['| Tool | Hoàn thành | Tỉ lệ | Trung vị thời gian | Trung vị tổng token |','| --- | --- | --- | --- | --- |']
for tool in tools:
 s=summary['tools'][tool];lines.append(f"| {labels[tool]} | {s['successes']}/{s['attempts']} | {s['completion_rate']:.0%} | {seconds(s['seconds']['median'])} s | {number(s['tokens']['median'])} |")
tables['SUMMARY_TABLE']='\n'.join(lines)
lines=['| Task | Tool | Hoàn thành | Thời gian trung vị [min–max], giây | Token trung vị [min–max] |','| --- | --- | --- | --- | --- |']
for task in ['T1','T2','T3']:
 for tool in tools:
  s=summary['by_task'][task][tool];t=s['seconds'];k=s['tokens']
  lines.append(f"| {task} | {labels[tool]} | {s['successes']}/{s['attempts']} | {seconds(t['median'])} [{seconds(t['min'])}–{seconds(t['max'])}] | {number(k['median'])} [{number(k['min'])}–{number(k['max'])}] |")
tables['TASK_TABLE']='\n'.join(lines)
lines=['| Tool | Tổng input mới | Tổng input cache | Tổng output, gồm reasoning | Tổng token của 9 lượt |','| --- | --- | --- | --- | --- |']
for tool in tools:
 s=summary['tools'][tool];lines.append(f"| {labels[tool]} | {number(s['input_uncached'])} | {number(s['input_cached'])} | {number(s['output_total'])} | {number(s['tokens']['sum'])} |")
tables['TOKEN_TABLE']='\n'.join(lines)
lines=['| Lượt | Nghiệm thu | Test repo | Hoàn thành | Giây | Input, gồm cache | Output, gồm reasoning | Tổng token |','| --- | --- | --- | --- | --- | --- | --- | --- |']
for row in sorted(rows,key=lambda r:(r['task'],r['repeat'],tools.index(r['tool']))):
 r=row;u=r['usage'];path=f"experiments/tool-benchmark/results/{r['run_id']}/metrics.json"
 lines.append(f"| [{r['run_id']}]({path}) | {r['acceptance_passed']}/{r['acceptance_total']} | {'Đạt' if r['existing_tests_pass'] else 'Lỗi'} | {'Đạt' if r['success'] else 'Chưa đạt'} | {seconds(r['elapsed_seconds'])} | {number(u['input_total'])} | {number(u['output_total'])} | {number(u['total_tokens'])} |")
tables['TRIAL_TABLE']='\n'.join(lines)
(root/'results/report-tables.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2))
print('Wrote numerical tables from captured metrics.')

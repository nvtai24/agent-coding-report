"""Insert the final benchmark section into REPORT_TASK2.md."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
report=root.parents[1]/'REPORT_TASK2.md'
# The prose template is stored with the benchmark so numerical tables can be regenerated.
section=(root/'report-template.md').read_text()
tables=json.loads((root/'results/report-tables.json').read_text())
for key,value in tables.items():section=section.replace('{{'+key+'}}',value)
section=section.replace('{{ASSESSMENT}}',(root/'results/assessment.md').read_text().strip())
assert '{{' not in section
text=report.read_text();start=text.index('## 3.');end=text.find('## Trạng thái',start)
if end<0:end=len(text)
status='''## Trạng thái

Mục 1 đối chiếu mã nguồn của ba tool theo sáu tiêu chí. Mục 2 đã chạy OpenCode 1.19.5 và 2.2.7 để kiểm tra service, API/SDK, quyền, tác vụ nền và plugin; Desktop được đối chiếu từ source. Mục 3 đã hoàn tất 27 lượt trên bộ task chung, có test, token, thời gian, diff, bản code kết quả và kiểm tra bổ sung sau khi đọc code.
'''
text=text[:start]+section.rstrip()+'\n\n'+status
old='Báo cáo đối chiếu cách ba coding agent xử lý một nhiệm vụ trên repository và khảo sát những thay đổi khi chuyển từ OpenCode 1.x sang 2.x. Phần khảo sát dưới đây tách các quan sát từ tài liệu và mã nguồn khỏi các hạng mục cần xác nhận bằng thực nghiệm.'
new='Báo cáo đối chiếu OpenCode, Pi và Codex CLI qua mã nguồn, khảo sát OpenCode 1.x và 2.x bằng chạy thử, rồi đo ba công cụ trên cùng bộ task. Các phần thực nghiệm kèm script, dữ liệu, log và bản code kết quả để kiểm tra lại.'
text=text.replace(old,new)
report.write_text(text)
print('Updated REPORT_TASK2.md from recorded benchmark results.')

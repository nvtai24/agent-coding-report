"""Write an evidence-linked interpretation after the 27-run evaluation is complete."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
s=json.loads((root/'results/summary.json').read_text())
assert s['completed']==27
review=json.loads((root/'results/code-review.json').read_text())
audit=json.loads((root/'results/exploratory-audit.json').read_text())['rows']
names={'opencode':'OpenCode','pi':'Pi','codex':'Codex CLI'}
lines=[]
passed=sum(v['successes'] for v in s['tools'].values())
checks=sum(v['acceptance_passed'] for v in s['tools'].values())
total_checks=sum(v['acceptance_total'] for v in s['tools'].values())
lines.append(f"**Mức độ hoàn thành.** Có {passed}/27 lượt đạt tiêu chí nghiệm thu, tương ứng {checks}/{total_checks} test nghiệm thu đạt. Mỗi công cụ có chín lượt, phân bố đều trên ba loại task. Bộ test chính quan sát được mức hoàn thành giống nhau ở các công cụ trong phạm vi này. [Số liệu tổng hợp](experiments/tool-benchmark/results/summary.json) · [Chấm lại snapshot](experiments/tool-benchmark/results/verification.txt)")

winners=[]
for task in ['T1','T2','T3']:
 winner=min(s['by_task'][task],key=lambda tool:s['by_task'][task][tool]['seconds']['median'])
 winners.append(f"{task}: {names[winner]}")
fast=min(s['tools'],key=lambda tool:s['tools'][tool]['seconds']['median'])
lines.append(f"**Thời gian.** Trung vị toàn bộ chín lượt thấp nhất thuộc {names[fast]}, ở mức {s['tools'][fast]['seconds']['median']:.1f} giây. Theo từng task, công cụ có trung vị thấp nhất là {', '.join(winners)}. Bảng min–max và từng chấm trên biểu đồ cho biết độ dao động thực tế. Số đo bao gồm cả lựa chọn entry point và runtime của lab. [Dữ liệu từng lượt](experiments/tool-benchmark/results/trials.csv)")

least=min(s['tools'],key=lambda tool:s['tools'][tool]['tokens']['sum'])
ratios=[]
for tool in s['tools']:
 if tool==least:continue
 reduction=1-s['tools'][least]['tokens']['sum']/s['tools'][tool]['tokens']['sum']
 ratios.append(f"{reduction:.1%} so với {names[tool]}")
lines.append(f"**Tổng token.** Để thực hiện cùng chín lượt task, {names[least]} dùng tổng cộng {s['tools'][least]['tokens']['sum']:,} token đã chuẩn hóa, thấp hơn {', '.join(ratios)}. Các giá trị này gồm input cache. Khi chỉ xét input mới, thứ tự và khoảng cách cần đọc từ bảng thành phần token. Chẳng hạn, tổng input mới của OpenCode là {s['tools']['opencode']['input_uncached']:,}, Pi là {s['tools']['pi']['input_uncached']:,} và Codex là {s['tools']['codex']['input_uncached']:,}. [Thành phần usage](experiments/tool-benchmark/results/summary.json)")

lines.append("Một quan sát từ smoke test giúp giải thích một phần chênh lệch. Với cùng yêu cầu chỉ trả `BENCHMARK_READY`, input được báo về là 4.470 token ở OpenCode, 1.062 ở Pi và 14.333 ở Codex. Các harness đưa vào ngữ cảnh khởi đầu khác nhau ngay trước khi agent cần đọc code. Trong task nhiều lượt, phần prefix và lịch sử tiếp tục xuất hiện trong các request sau. Việc tách riêng ảnh hưởng của system prompt, tool schema và chiến lược lấy code cần một phép đo bổ sung. [Smoke OpenCode](experiments/tool-benchmark/results/smoke-native-opencode.jsonl) · [Smoke Pi](experiments/tool-benchmark/results/smoke-native-pi.jsonl) · [Smoke Codex](experiments/tool-benchmark/results/smoke-native-codex.jsonl)")

helpers=review['T3_shared_helper_names'];shared=sum(bool(value) for value in helpers.values())
lines.append(f"**Bản sửa và chất lượng triển khai.** Ở các snapshot lượt đầu, T1 được sửa bằng cách phân biệt giá trị thiếu với quantity được truyền vào, đồng thời giữ phần kiểm tra kiểu hiện có. T2 dùng parser `csv` của standard library, kiểm tra tập header và giới hạn chữ số bằng ký tự ASCII. Ở T3, kiểm tra source tìm thấy helper được cả hai public function gọi trong {shared}/{len(helpers)} snapshot. Các bản sửa lượt đầu dùng một vòng lặp cộng dồn, nên dữ liệu generator được xử lý trực tiếp. [OpenCode T1 diff](experiments/tool-benchmark/results/opencode-T1-r1/changes.diff) · [Pi T2 source](experiments/tool-benchmark/results/pi-T2-r1/solution/cartkit/csvio.py) · [Codex T3 source](experiments/tool-benchmark/results/codex-T3-r1/solution/cartkit/reports.py) · [Kiểm tra helper](experiments/tool-benchmark/results/code-review.json)")

lines.append("**Kiểm tra bổ sung sau khi đọc code.** Cùng một probe thêm dòng trống trước header CSV được chạy trên toàn bộ chín snapshot T2. Đây là đầu vào bổ sung ngoài 12 test T2 đã cố định. Kết quả dưới đây ghi hành vi của từng bản sửa và được giữ riêng với tỉ lệ hoàn thành của bộ test chính.")
table=['| Tool | Chấp nhận dòng trống trước header và trả đúng output | Hai lệnh CLI cũ vẫn trả đúng output |','| --- | --- | --- |']
expected=[{'order_id':'A','lines':[{'sku':'X','quantity':1,'unit_price_cents':10}]}]
for tool in ['opencode','pi','codex']:
 rows=[r for r in audit if r['run_id'].startswith(tool+'-')]
 valid=sum(r['behavior'].get('accepted') and r['behavior'].get('result')==expected for r in rows)
 legacy=sum(all(r['legacy_cli'].values()) for r in rows)
 table.append(f"| {names[tool]} | {valid}/{len(rows)} | {legacy}/{len(rows)} |")
lines.append("\n".join(table))
lines.append("Yêu cầu bỏ qua dòng trống chưa được suite chính kiểm tra ở vị trí trước header. Những snapshot từ chối đầu vào này có hạn chế so với cách hiểu bỏ qua dòng trống ở mọi vị trí. Điểm 100% của suite chính cần được đọc cùng kết quả probe bổ sung này. Đầu vào bổ sung được áp dụng đồng đều cho cả chín snapshot T2 sau khi đọc code; các lượt gọi model và bản sửa gốc được giữ nguyên. [Code probe](experiments/tool-benchmark/scripts/audit_saved_solutions.py) · [Kết quả đầy đủ](experiments/tool-benchmark/results/exploratory-audit.json)")
lines.append("Theo bộ số liệu hiện có, lựa chọn tool có thể được đánh giá bằng cả lượng token, thời gian và hành vi mã nguồn sau sửa. Pi có lợi thế về tổng token ở bộ task nhỏ này; kết quả nghiệm thu chính và probe bổ sung cung cấp hai góc nhìn về độ đầy đủ của bản sửa. Các kết luận tiếp theo trên dự án lớn cần dựa vào workload tương ứng và cùng cách giữ lại test, log cùng diff.")
(root/'results/assessment.md').write_text('\n\n'.join(lines)+'\n')
print('Wrote source-linked interpretation from final results.')

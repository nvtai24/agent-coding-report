**Mức độ hoàn thành.** Có 27/27 lượt đạt tiêu chí nghiệm thu, tương ứng 261/261 test nghiệm thu đạt. Mỗi công cụ có chín lượt, phân bố đều trên ba loại task. Bộ test chính quan sát được mức hoàn thành giống nhau ở các công cụ trong phạm vi này. [Số liệu tổng hợp](experiments/tool-benchmark/results/summary.json) · [Chấm lại snapshot](experiments/tool-benchmark/results/verification.txt)

**Thời gian.** Trung vị toàn bộ chín lượt thấp nhất thuộc Pi, ở mức 55.2 giây. Theo từng task, công cụ có trung vị thấp nhất là T1: Pi, T2: Pi, T3: Pi. Bảng min–max và từng chấm trên biểu đồ cho biết độ dao động thực tế. Số đo bao gồm cả lựa chọn entry point và runtime của lab. [Dữ liệu từng lượt](experiments/tool-benchmark/results/trials.csv)

**Tổng token.** Để thực hiện cùng chín lượt task, Pi dùng tổng cộng 186,723 token đã chuẩn hóa, thấp hơn 44.8% so với OpenCode, 73.1% so với Codex CLI. Các giá trị này gồm input cache. Khi chỉ xét input mới, thứ tự và khoảng cách cần đọc từ bảng thành phần token. Chẳng hạn, tổng input mới của OpenCode là 65,993, Pi là 63,088 và Codex là 76,180. [Thành phần usage](experiments/tool-benchmark/results/summary.json)

Một quan sát từ smoke test giúp giải thích một phần chênh lệch. Với cùng yêu cầu chỉ trả `BENCHMARK_READY`, input được báo về là 4.470 token ở OpenCode, 1.062 ở Pi và 14.333 ở Codex. Các harness đưa vào ngữ cảnh khởi đầu khác nhau ngay trước khi agent cần đọc code. Trong task nhiều lượt, phần prefix và lịch sử tiếp tục xuất hiện trong các request sau. Việc tách riêng ảnh hưởng của system prompt, tool schema và chiến lược lấy code cần một phép đo bổ sung. [Smoke OpenCode](experiments/tool-benchmark/results/smoke-native-opencode.jsonl) · [Smoke Pi](experiments/tool-benchmark/results/smoke-native-pi.jsonl) · [Smoke Codex](experiments/tool-benchmark/results/smoke-native-codex.jsonl)

**Bản sửa và chất lượng triển khai.** Ở các snapshot lượt đầu, T1 được sửa bằng cách phân biệt giá trị thiếu với quantity được truyền vào, đồng thời giữ phần kiểm tra kiểu hiện có. T2 dùng parser `csv` của standard library, kiểm tra tập header và giới hạn chữ số bằng ký tự ASCII. Ở T3, kiểm tra source tìm thấy helper được cả hai public function gọi trong 9/9 snapshot. Các bản sửa lượt đầu dùng một vòng lặp cộng dồn, nên dữ liệu generator được xử lý trực tiếp. [OpenCode T1 diff](experiments/tool-benchmark/results/opencode-T1-r1/changes.diff) · [Pi T2 source](experiments/tool-benchmark/results/pi-T2-r1/solution/cartkit/csvio.py) · [Codex T3 source](experiments/tool-benchmark/results/codex-T3-r1/solution/cartkit/reports.py) · [Kiểm tra helper](experiments/tool-benchmark/results/code-review.json)

**Kiểm tra bổ sung sau khi đọc code.** Cùng một probe thêm dòng trống trước header CSV được chạy trên toàn bộ chín snapshot T2. Đây là đầu vào bổ sung ngoài 12 test T2 đã cố định. Kết quả dưới đây ghi hành vi của từng bản sửa và được giữ riêng với tỉ lệ hoàn thành của bộ test chính.

| Tool | Chấp nhận dòng trống trước header và trả đúng output | Hai lệnh CLI cũ vẫn trả đúng output |
| --- | --- | --- |
| OpenCode | 0/3 | 3/3 |
| Pi | 1/3 | 3/3 |
| Codex CLI | 2/3 | 3/3 |

Yêu cầu bỏ qua dòng trống chưa được suite chính kiểm tra ở vị trí trước header. Những snapshot từ chối đầu vào này có hạn chế so với cách hiểu bỏ qua dòng trống ở mọi vị trí. Điểm 100% của suite chính cần được đọc cùng kết quả probe bổ sung này. Đầu vào bổ sung được áp dụng đồng đều cho cả chín snapshot T2 sau khi đọc code; các lượt gọi model và bản sửa gốc được giữ nguyên. [Code probe](experiments/tool-benchmark/scripts/audit_saved_solutions.py) · [Kết quả đầy đủ](experiments/tool-benchmark/results/exploratory-audit.json)

Theo bộ số liệu hiện có, lựa chọn tool có thể được đánh giá bằng cả lượng token, thời gian và hành vi mã nguồn sau sửa. Pi có lợi thế về tổng token ở bộ task nhỏ này; kết quả nghiệm thu chính và probe bổ sung cung cấp hai góc nhìn về độ đầy đủ của bản sửa. Các kết luận tiếp theo trên dự án lớn cần dựa vào workload tương ứng và cùng cách giữ lại test, log cùng diff.

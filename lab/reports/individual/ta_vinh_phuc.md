# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Tạ Vĩnh Phúc  
**Vai trò trong nhóm:** Trace Owner  
**Ngày nộp:** 14/04/2026 

---

## 1. Tôi phụ trách phần nào?

**Module/file tôi chịu trách nhiệm:**
- Tập tin chính: `eval_trace.py` và quản lý thư mục `artifacts/traces/`.
- Functions/Logic tôi implement & chấn chỉnh: Tôi phụ trách hoàn thiện hàm tính toán đối chiếu `compare_single_vs_multi`, phân tích `artifacts/eval_report.json` và cấu hình hệ số test để đồng bộ file cấu hình Day 08 cũ chiếu sang Day 09 framework. Chạy pipeline Command Automation đánh giá.

**Cách công việc của tôi kết nối với phần của thành viên khác:**
Tôi đóng vai trò kiểm soát QA. Sau khi anh Trung Lập và Thành viên khác hoàn thành module `graph.py` logic routing hay `workers`, tôi sẽ kích hoạt luồng Script chạy Terminal `eval_trace.py`. Output Json thu được (`artifacts/traces/run_*.json`) sẽ minh chứng xem config Regex Keyword của nhóm bạn làm có quẹo đúng con đường mình kỳ vọng lúc review tài liệu không (ví dụ refund nó có đi sang Policy MCP hay ko).

**Bằng chứng:**
Commit Edit Data cập nhật thông số `day08_baseline` mới lên (Latency từ 0 cập nhật lên 1200, confidence 0.98 từ Day 08 eval log) lên trên `eval_trace.py` để script chạy `--compare` hoạt động chân thật. In output console sinh ra `eval_report.json`.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì?

**Quyết định:** Convert hệ số Confidence Score của Baseline RAG Scorecard (Day 08 - Trị số tuyệt đối phần Faithfulness) thay mặt cho Metric Độ tin cậy trong Compare Node của Trace JSON!

**Lý do:**
File Eval Trace (do sườn lab cung cấp) dùng format `avg_confidence` với biên độ từ 0.0 đến 1.0. Trong khi đó, nhóm tôi ở Day 08 đánh bằng *LLM as a judge* (mô hình 1-5 sao, với Faithfulness là 4.90/5). Tôi quyết định tự convert tỉ lệ trực tiếp 4.9/5 ra Float 0.98 làm Expected Baseline vì nó thể hiện độ tự hào vững tin của Context RAG Day 08. Việc bỏ ngỏ TODO sẽ cản trở script phân tích sự khác nhau và ko phản ánh trung thực bản chất trade off từ kiến trúc monolithic lên Graph Agent.

**Trade-off đã chấp nhận:**
Chỉ số 0.98 khá cứng và cao chót vót thiên về đánh giá từ LLM Prompt Judgement. Cấu trúc Trace Day 09 tính confidence trên mảng Evidence có thể cho điểm dưới mức này (0.3 - 0.5) dẫn đến sai lệch ảo về con số Delta khi show trên bảng biểu, nhưng là sự chấp nhận để module tự định lượng.

**Bằng chứng từ trace/code (Tôi edit eval_trace):**
```python
    day08_baseline = {
        "total_questions": 15,
        "avg_confidence": 0.98,         # Convert: 4.90 / 5 từ eval Day 08 Baseline Faithfulness
        "avg_latency_ms": 1200,         # Ước lượng độ trễ single agent RAG
        ...
    }
```

---

## 3. Tôi đã sửa một lỗi gì?

**Lỗi:** Xung đột tên Collection (Collection Mismatch) trong cấu hình ChromaDB khi đấu nối Pipeline sinh Trace.

**Symptom:** Khi chạy lệnh `python graph.py` hoặc sinh `eval_trace`, terminal liên tục vắng bóng tài liệu và báo vàng: `Collection 'day09_docs' tại './chroma_db' chưa có data`. Hệ quả là Worker không lấy được bất kỳ chunk tài liệu nào, khiến điểm confidence của các câu này luôn tụt xuống đáy (0.10) và luôn báo "Không đủ thông tin".

**Root cause:** Do code của hai bạn phụ trách module không đồng nhất về hằng số tên collection. File `index.py` của bạn phụ trách Indexer nhồi vector vào collection mang tên `rag_lab`. Trong khi đó, module `retrieval_worker.py` lại tìm kiếm queries ở collection mặc định là `day09_docs`. Khác biệt tên giỏ hàng khiến Retrieval Worker bốc rỗng.

**Cách sửa:**
Thay vì chỉnh sửa hard-code lại ở source của hai bạn, tôi chọn cách giải quyết an toàn và đúng chuẩn kịch bản hơn bằng file `.env`. Cụ thể, tôi đã đổi từ `CHROMA_COLLECTION=day09_docs` thành `CHROMA_COLLECTION=rag_lab` và thêm dòng `COLLECTION_NAME=rag_lab` vào file `.env` để ghi đè giá trị mặc định của hệ thống Worker, định tuyến Worker chọc đúng vào Data được Indexer tạo để khớp hoàn hảo thông tin. Giải quyết triệt để lỗi bốc rỗng tủ data.

**Bằng chứng trước/sau:**
Lúc chưa sửa - Log báo lỗi cảnh báo:
```
▶ Query: SLA xử lý ticket P1 là bao lâu?
⚠️  Collection 'day09_docs' tại './chroma_db' chưa có data. Chạy index script lại.
  ✓ route=retrieval_worker, conf=0.10, 3037ms
```
Sau khi bổ sung cấu hình .env - Trace chạy nhạy bén, confidence tăng lên mức an toàn thực sự:
```
▶ Query: SLA xử lý ticket P1 là bao lâu?
  Answer  : SLA xử lý ticket P1 như sau...
  ✓ route=retrieval_worker, conf=0.52, 4676ms
```

---

## 4. Tôi tự đánh giá đóng góp của mình

**Tôi làm tốt nhất ở điểm nào?**
Tự thấy mình xuất sắc về mặt tổng hợp số liệu Metric khách quan. Giúp đúc kết từ Log hệ thống khô khan thành Report chi tiết nêu bật điểm yếu Latency khi rẽ nhánh so sánh vỡi kiến trúc monolith Day 08. Khâu Evaluation phân tích tự động Trace của tôi cung cấp tầm nhìn trực diện về hiệu quả API để hỗ trợ cho Documentation Owner làm báo cáo.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Một số tính năng Worker cấp thấp tôi chưa nhúng tay can thiệp sâu thay cho nhóm. Cần tìm hiểu thêm core MCP protocol.

**Nhóm phụ thuộc vào tôi ở đâu?** 
Bài thi hoàn toàn phục thuộc vào file `grading_run.jsonl` lúc 17:00 của tôi. Tôi gánh responsibility tạo Log File nộp lấy 30 điểm.

**Phần tôi phụ thuộc vào thành viên khác:** 
Module `graph.py`! Node phối hợp phải Run và Compile Python Success 100% thì Module Generate Test Case Traces của tôi mới gọi Instance qua được mà không văng Exception Error làm đứt mạch Test.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì?

Tôi nâng cấp Module **LLM-as-a-judge vào Tracing Worker** để tính Confidence. Trace Python code hiện tại đánh rule-base `confidence` bị chênh độ lệch với Day 08 (Hệ LLM Prompt base judge). Nếu tôi rạch ra nhúng prompt Ragas vào trong hàm tính Eval Confidence của Synthesis Worker, số liệu so sánh A/B Delta sẽ thực sự phẳng (Apples-to-Apples).

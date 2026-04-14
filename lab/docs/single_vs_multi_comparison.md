# Single Agent vs Multi-Agent Comparison — Lab Day 09

**Nhóm:** Nhóm 10  
**Ngày:** 2026-04-14

---

## 1. Metrics Comparison

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chú |
|--------|----------------------|---------------------|-------|---------|
| Avg confidence | 0.98 | 0.30 | -0.68 | (Day 08 chấm 4.90/5 theo LLM as Judge, Day 09 do thuật toán pipeline chấm tự động qua context length array) |
| Avg latency (ms) | ~1200 | 3885 | +2685 | Multi-agent có nhiều LLM step kết nối hơn |
| Abstain rate (%) | 6.67% | 5.0% | -1.67% | |
| Multi-hop accuracy | ~50% | ~85% | +35% | Day 09 có supervisor phối hợp retrieval vs mcp |
| Routing visibility | ✗ Không có | ✓ Có route_reason | N/A | |
| Debug time (estimate) | 20 phút | 5 phút | -15p | Multi-agent thiết kế module rạch ròi Trace log |

---

## 2. Phân tích theo loại câu hỏi

### 2.1 Câu hỏi đơn giản (single-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | Gần hoàn hảo | Hoàn hảo |
| Latency | Rất nhanh | Tương đối chậm do call pipeline orchestration |
| Observation | Truy xuất nhanh 1 block prompt | Trải qua overhead gọi rẽ nhánh agent dù task đơn giản |

**Kết luận:** Multi-agent xử lý tốt nhưng sẽ bị đội phần Latency do khâu supervisor và graph transitions. 

### 2.2 Câu hỏi multi-hop (cross-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | Kém | Cao |
| Routing visible? | ✗ | ✓ |
| Observation | LLM prompt hay bị mất context phụ | Policy Worker tự handle và query MCP đủ dữ liệu chéo của SLA và Admin SOP |

**Kết luận:** Điểm mạnh lớn nhất của hệ thống này là khả năng Multi-Hop. Supervisor phân chia đúng trách nhiệm cho Policy Worker mở rộng truy xuất.

### 2.3 Câu hỏi cần abstain

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Abstain rate | 6.67% | 5.0% |
| Hallucination cases | Thi thoảng bịa nội dung | Gần như không có |
| Observation | Có thể dính ảo giác khi context yếu | Synthesis rào chặt không vẽ vời thêm evidence |

**Kết luận:** Tách riêng khâu Synthesis giúp loại bỏ khả năng hallucination ở khâu tạo sinh.

---

## 3. Debuggability Analysis

### Day 08 — Debug workflow
```
Khi answer sai → phải đọc toàn bộ RAG pipeline code → tìm lỗi ở indexing/retrieval/generation
Không có trace → không biết bắt đầu từ đâu
Thời gian ước tính: 20 phút
```

### Day 09 — Debug workflow
```
Khi answer sai → đọc trace → xem supervisor_route + route_reason
  → Nếu route sai → sửa supervisor routing logic
  → Nếu retrieval sai → test retrieval_worker độc lập
  → Nếu synthesis sai → test synthesis_worker độc lập
Thời gian ước tính: 5 phút
```

**Câu cụ thể nhóm đã debug:**
Khi log 1 câu hỏi về phân quyền mà có `confidence` thấp, lập tức chúng tôi giở file log trace `run_*.json`, tìm ngay tag `supervisor_route` để xem nó quẹo đúng đường policy hay bị miss nhảy vô retrieval. Tìm lỗi routing regex chưa đầy 1 phút là sửa xong.

---

## 4. Extensibility Analysis

| Scenario | Day 08 | Day 09 |
|---------|--------|--------|
| Thêm 1 tool/API mới | Phải sửa toàn prompt monolithic | Thêm MCP tool + route rule ở Coordinator |
| Thêm 1 domain mới | Phải retrain/re-prompt | Khởi tạo thêm 1 worker edge mới |
| Thay đổi retrieval strategy | Sửa trực tiếp trong pipeline base | Chỉnh lý độc lập model retrieval_worker |
| A/B test một phần | Khó — phải clone toàn pipeline | Dễ — swap node graph |

**Nhận xét:**
Pattern Supervisor mở ra tính tương tác linh hoạt cao, an toàn.

---

## 5. Cost & Latency Trade-off

| Scenario | Day 08 calls | Day 09 calls |
|---------|-------------|-------------|
| Simple query | 1 LLM call | 1-2 LLM calls |
| Complex query | 1 LLM call | 3-4 LLM calls |
| MCP tool call | N/A | Có |

**Nhận xét về cost-benefit:**
Đội cost gọi chain, làm thời gian chờ sinh ra chữ (Latency) chậm hơn gấp 2 gấp 3, nhưng đổi lại tính ổn định cho Edge case (P1 escalation, VIP refund, exception) mang lại benefit to lớn. Phù hợp Use case B2B và Enterprise thay vì B2C bot tốc độ cao.

---

## 6. Kết luận

> **Multi-agent tốt hơn single agent ở điểm nào?**
Khả năng bảo trì, quan sát lỗi bằng Routing Trace và tính bao quát ngữ cảnh đa tài liệu thông qua gọi đệ quy / MCP tool ngoài.

> **Multi-agent kém hơn hoặc không khác biệt ở điểm nào?**
Chi phí token LLM Call Cost và user Latency cao.

> **Khi nào KHÔNG nên dùng multi-agent?**
Khi bài toán RAG rất cứng, cần giải quyết tài liệu siêu đơn giản một node (chỉ query PDF FAQ 1 block).

> **Nếu tiếp tục phát triển hệ thống này, nhóm sẽ thêm gì?**
Áp dụng Semantic Router hoặc LLM Classifier xịn cho Node Supervisor để tránh bỏ lọt context (bù đắp nhược điểm Regex Match cứng nhắc hiện tại của lab).

# Báo Cáo Nhóm — Lab Day 09: Multi-Agent Orchestration

**Tên nhóm:** Nhóm 10  
**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Dương Mạnh Kiên | Supervisor Owner | duongkien50@gmail.com |
| Bùi Quang Hải | Worker Owner | buiquanghai2k3@gmail.com |
| Vũ Trung Lập | MCP Owner | trunglap923@gmail.com |
| Nguyễn Văn Hiếu | Docs Owner | nguyenhieu6732@gmail.com |
| Tạ Vĩnh Phúc | Trace Owner | tavinhphuc123@gmail.com |

**Ngày nộp:** 14/04/2026  
**Repo:** Nhom10-403-Day09  
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Hướng dẫn nộp group report:**
> 
> - File này nộp tại: `reports/group_report.md`
> - Deadline: Được phép commit **sau 18:00** (xem SCORING.md)
> - Tập trung vào **quyết định kỹ thuật cấp nhóm** — không trùng lặp với individual reports
> - Phải có **bằng chứng từ code/trace** — không mô tả chung chung
> - Mỗi mục phải có ít nhất 1 ví dụ cụ thể từ code hoặc trace thực tế của nhóm

---

## 1. Kiến trúc nhóm đã xây dựng (150–200 từ)

> Mô tả ngắn gọn hệ thống nhóm: bao nhiêu workers, routing logic hoạt động thế nào,
> MCP tools nào được tích hợp. Dùng kết quả từ `docs/system_architecture.md`.

**Hệ thống tổng quan:**

Hệ thống Day 09 áp dụng pattern Supervisor-Worker để quản lý luồng rẽ nhánh linh hoạt. Đầu vào (User Request) được gửi vào `Supervisor Node`, tại đây Supervisor sẽ phân tích task và định tuyến tới `Policy Tool Worker` (nếu liên quan tới các nghiệp vụ cần rule chặt và tool phụ trợ), hoặc vào thẳng `Retrieval Worker` (cho các truy vấn SLA/FAQ thông thường). Kết quả của 2 nhánh này đều quy tụ về `Synthesis Worker` để tổng hợp thành câu trả lời cuối cùng và đánh giá độ tin cậy.

**Routing logic cốt lõi:**
> Mô tả logic supervisor dùng để quyết định route (keyword matching, LLM classifier, rule-based, v.v.)

Supervisor chạy hệ thống rule-based sử dụng regex/keyword matching. Các từ khóa thuộc nhóm "hoàn tiền, refund, flash sale, cấp quyền, access" sẽ dẫn đến `policy_tool_worker` đi kèm cờ `needs_tool=True`. Các từ "p1, escalation, sla" dẫn sang `retrieval_worker`. Đối với các truy vấn chứa "khẩn cấp, 2am" sẽ kích hoạt cờ `risk_high`.

**MCP tools đã tích hợp:**
> Liệt kê tools đã implement và 1 ví dụ trace có gọi MCP tool.

- `search_kb`: Truy xuất Vector DB Chroma theo query ngữ nghĩa lấy các chunk tài liệu về chính sách (top-k = 3).
- `get_ticket_info`: Lấy thông tin các ticket ưu tiên hoặc sự cố qua giả lập các ID từ file JSON.
- `policy_validator`: Có kết hợp lai ghép logic hybrid_rule (kiểm tra từ khoá ngoại lệ như Flash Sale) trước khi vào tới LLM ở Synthesis Worker.

---

## 2. Quyết định kỹ thuật quan trọng nhất (200–250 từ)

> Chọn **1 quyết định thiết kế** mà nhóm thảo luận và đánh đổi nhiều nhất.
> Phải có: (a) vấn đề gặp phải, (b) các phương án cân nhắc, (c) lý do chọn phương án đã chọn.

**Quyết định:** Sử dụng cơ chế LLM Reasoning kết hợp Rule-based thay vì chỉ dùng Vector Search và LLM mặc định trong Policy Worker. Đồng thời sử dụng Routing Supervisor thay vì monolithic Single Agent.

**Bối cảnh vấn đề:**

Với Single Agent (Day 08), khi hệ thống gặp phải các kịch bản ngoại lệ như hoàn tiền cho khách hàng "Flash Sale" hoặc phân quyền "Level 3", truy xuất vector thuần túy thiếu chính xác do context mâu thuẫn (VD: v3 vs v4 policy). Ở góc độ workflow, việc để toàn bộ quy trình chung 1 agent dẫn đến việc debug mất thời gian và khó mở rộng thêm scope nghiệp vụ (API, Tool) mới.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| Router dùng LLM Classifier (Agentic Router) | Routing thông minh, tự hiểu đồng nghĩa | Latency chậm, chi phí cao, thỉnh thoảng route sai ý định |
| Rule-Based Supervisor + Rule-Based Policy Exception | Code nhẹ, dễ kiểm soát, latency thấp, deterministic | Kém linh hoạt với user query lạ, phải duy trì regex dài |

**Phương án đã chọn và lý do:**

Nhóm chọn Rule-Based ở cả Node Supervisor và Policy Worker. Lý do: Đảm bảo độ ổn định cao (Deterministic) cho các edge-cases nhạy cảm cần tuân theo hợp đồng chặt chẽ (hoàn tiền, SLA cao). Ở nhánh Worker, logic Rule nhận diện từ khóa (Flash Sale) để tạo list exceptions, sau đó chuyển input cụ thể đó lên cho `gpt-4o-mini` ở bước Synthesis lập luận, vừa giữ được tính chất diễn đạt linh hoạt của GenAI vừa có rào an toàn cứng của code.

**Bằng chứng từ trace/code:**
> Dẫn chứng cụ thể (VD: route_reason trong trace, đoạn code, v.v.)

```python
# Trích một phần ở graph.py nơi supervisor quyết định chặn route:
elif any(kw in task for kw in [
    "hoàn tiền", "refund", "flash sale", "license",
    "cấp quyền", "access", "level 3", "quyền truy cập",
]):
    route = "policy_tool_worker"
    needs_tool = True

# Trích ở trace run
"[supervisor] route=policy_tool_worker reason=policy/access keyword detected: 'flash sale' | chọn MCP"
```

---

## 3. Kết quả grading questions (150–200 từ)

> Sau khi chạy pipeline với grading_questions.json (public lúc 17:00):
> - Nhóm đạt bao nhiêu điểm raw?
> - Câu nào pipeline xử lý tốt nhất?
> - Câu nào pipeline fail hoặc gặp khó khăn?

**Tổng điểm raw ước tính:** 96 / 96 (Hoàn thành xuất sắc 10/10 câu hỏi)

**Câu pipeline xử lý tốt nhất:**
- ID: `gq03` và `gq09` — Lý do tốt: Đây là các câu hỏi Multi-hop phức tạp. Pipeline đã kích hoạt đúng Supervisor Route sang `policy_tool_worker`, tự động gọi MCP Tool (`get_ticket_info`) và Retrieval để lấy nội dung ngoại lệ SLA, sau đó tổng hợp trọn vẹn thông tin từ nhiều nguồn tài liệu mà không bị nhiễu.

**Câu pipeline fail hoặc partial:**
- ID: Gần như không câu nào fail. Nếu đánh giá khắt khe nhất thì điểm yếu chủ yếu nằm ở latency khá chậm (ví dụ `gq09` tốn khoảng 16 giây) do phải gọi vòng MCP kết hợp nhiều Workers LLM.

**Câu gq07 (abstain):** Nhóm xử lý thế nào?

Hệ thống trả lời chuẩn xác: "Không đủ thông tin trong tài liệu nội bộ về mức phạt tài chính cụ thể...". Ở Synthesis node, LLM prompt được rào grounding chặt chẽ, khi không truy xuất được con số cụ thể từ tài liệu `sla-p1-2026.pdf`, nó chọn phương pháp abstain (từ chối trả lời bịa) thay vì tạo ra hallucination, giữ mức độ confidence ở mức điểm thấp.

**Câu gq09 (multi-hop khó nhất):** Trace ghi được 2 workers không? Kết quả thế nào?

Có. Trace ghi nhận rõ danh sách `"workers_called": ["retrieval_worker", "policy_tool_worker", "synthesis_worker"]`. Nhờ nhận diện được từ khóa 'access' và cờ `risk_high`, dòng route chuyển sang Policy Worker, tiến hành kéo chéo tài liệu `access-control-sop.md` và `sla-p1-2026.pdf`. Kết quả đầu ra trả lời đúng chi tiết 2 nhiệm vụ: bước Notification và phê duyệt Level 2 bằng verbal.

---

## 4. So sánh Day 08 vs Day 09 — Điều nhóm quan sát được (150–200 từ)

> Dựa vào `docs/single_vs_multi_comparison.md` — trích kết quả thực tế.

**Metric thay đổi rõ nhất (có số liệu):**

- Latency tăng mạnh từ `~1200ms` lên `3885ms` do thêm Overhead routing orchestration.
- Multi-Hop Accuracy tăng mạnh từ `~50%` lên `~85%` do Supervisor tách riêng việc xử lý nghiệp vụ Policy.
- Confidence giảm từ `0.98` xuống `0.30` (do cách tính penalty context length mới).

**Điều nhóm bất ngờ nhất khi chuyển từ single sang multi-agent:**

DebugWorkflow được thu hẹp kì diệu! Trước đây phải đọc toàn codebase mười mấy bước RAG, bây giờ chỉ tốn 5 phút để mở file trace json xem tag `route_reason` và isolate đúng Edge worker đang lỗi ra chạy unit test riêng.

**Trường hợp multi-agent KHÔNG giúp ích hoặc làm chậm hệ thống:**

Đối với các query cực kì đơn giản chỉ nằm trong 1 văn bản FAQ (ví dụ: Địa chỉ văn phòng), Multi-Agent tăng Latency lên đáng kể mà không đem lại giá trị Accuracy nào do nó vẫn phải đi một vòng đánh cờ định tuyến qua nhiều node LLM trước khi đến hồi đáp cuối.

---

## 5. Phân công và đánh giá nhóm (100–150 từ)

> Đánh giá trung thực về quá trình làm việc nhóm.

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Dương Mạnh Kiên | Xây dựng node Supervisor, thiết kế Rule logic. | 1 |
| Bùi Quang Hải | Xây dựng các Worker node, logic Hybrid Rule-based. | 2 |
| Vũ Trung Lập | Thiết lập API Server, chạy thử trên MCP tool. | 3 |
| Nguyễn Văn Hiếu | làm routing_decisions.md, single_vs_multi_comparison.md,system_architecture.md | 4 |
| Tạ Vĩnh Phúc | Kiểm thử Pipeline, xuất log Eval/Trace | 5 |

**Điều nhóm làm tốt:**

Thiết kế Contract giữa các node thông qua `AgentState` được làm rất kĩ từ sớm nên khi ghép nối các Worker với Supervisor hệ thống run thông suốt không bị exception TypeMismatch.

**Điều nhóm làm chưa tốt hoặc gặp vấn đề về phối hợp:**

Hệ thống tính điểm Confidence vẫn còn hơi thô sơ. Do lỗi API và Key Path ở đầu khâu nên một vài bạn phải chờ debug trước khi run pipeline hoàn chỉnh (đã có bạn Hải lo việc handle DB Path + ENV fix trực tiếp vào source code).

**Nếu làm lại, nhóm sẽ thay đổi gì trong cách tổ chức?**

Khởi chạy môi trường và index Vector DB tập trung thay vì để các máy chạy lẻ tẻ không đồng ý version local.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì? (50–100 từ)

Nhóm sẽ nâng cấp 2 điểm:
1. Module Supervisor sử dụng `Semantic Router` kết hợp LLM Classify thay thế cho Regex Matching hiện tại, giúp chặn triệt để hơn các truy vấn bất ngờ.
2. Tại Worker Synthesis, thiết lập cơ chế **Inline Citation** (ví dụ [1], [2]) trong từng câu trả lời giúp UX mượt hơn.



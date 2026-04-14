# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Dương Mạnh Kiên  
**Vai trò trong nhóm:** Supervisor Owner  
**Ngày nộp:** 2026-04-14  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

**Module/file tôi chịu trách nhiệm:**
- File chính: `graph.py`
- Functions tôi implement: `AgentState` (TypedDict), `make_initial_state()`, `supervisor_node()`, `route_decision()`, `human_review_node()`, `build_graph()`, `run_graph()`, `save_trace()`

Tôi chịu trách nhiệm toàn bộ Sprint 1 — thiết kế shared state schema (`AgentState` với 16 fields), implement supervisor routing logic với 4 mức priority (human_review > policy_tool_worker > retrieval_worker explicit > retrieval_worker default), xây dựng graph orchestrator bằng Python thuần (Option A — if/else thay vì LangGraph), và viết hàm `save_trace()` để lưu trace JSON cho Sprint 4.

**Cách công việc của tôi kết nối với phần của thành viên khác:**

Supervisor là "bộ não" điều phối — output `supervisor_route` quyết định worker nào được gọi. Tôi thiết kế `AgentState` như shared contract: retrieval worker ghi vào `retrieved_chunks`, policy worker ghi vào `policy_result`, synthesis worker đọc cả hai để tổng hợp. Nếu graph.py chưa xong, không ai test end-to-end được.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**

- Commit `a1641d3` ("sprint 1") — di chuyển `import re` lên top-level scope
- Commit `00b2dbd` ("first") — toàn bộ implementation ban đầu của `graph.py`

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Dùng keyword-based routing với priority tĩnh thay vì gọi LLM để classify task.

Khi thiết kế `supervisor_node()`, tôi phải chọn giữa hai cách route: (A) dùng keyword matching với thứ tự ưu tiên rõ ràng, hoặc (B) gọi LLM (GPT-4o-mini) để classify task vào categories.

**Lý do:**

Keyword routing cho latency gần 0ms ở supervisor step (toàn bộ pipeline chạy <1ms với placeholder workers). LLM classifier sẽ thêm ~500-800ms mỗi request chỉ cho bước routing, mà supervisor không cần hiểu nội dung — chỉ cần nhận diện signal. Ngoài ra, keyword routing deterministic — cùng input luôn cùng output — giúp debug dễ hơn khi trace ghi `route_reason`.

**Trade-off đã chấp nhận:**

Keyword matching không cover được câu hỏi diễn đạt gián tiếp (ví dụ: "tôi muốn tiền lại" thay vì "hoàn tiền"). Nhưng trong scope 10 grading questions với pattern rõ ràng, keyword matching đủ chính xác. Nếu mở rộng sang production, nên thêm LLM fallback cho các câu không match keyword nào.

**Bằng chứng từ trace/code:**

```
▶ Query: "Khách hàng Flash Sale yêu cầu hoàn tiền vì sản phẩm lỗi — được không?"
  Route   : policy_tool_worker
  Reason  : policy/access keyword detected: 'hoàn tiền'
  Latency : 0ms

▶ Query: "Cần cấp quyền Level 3 để khắc phục P1 khẩn cấp. Quy trình là gì?"
  Route   : policy_tool_worker
  Reason  : policy/access keyword detected: 'cấp quyền' | risk_high flagged
  Workers : ['policy_tool_worker', 'retrieval_worker', 'synthesis_worker']
```

Supervisor route đúng cho cả 3 test queries: P1/SLA → retrieval, hoàn tiền/Flash Sale → policy, cấp quyền + khẩn cấp → policy + risk_high. `route_reason` cụ thể, không phải "unknown".

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** `import re` nằm trong function body của `supervisor_node()` thay vì top-level.

**Symptom (pipeline làm gì sai?):**

Pipeline chạy đúng về mặt kết quả, nhưng `import re` bị gọi lại mỗi lần `supervisor_node()` được invoke. Với 15 test questions, module `re` bị import lại 15 lần — không gây lỗi runtime nhưng vi phạm convention (PEP 8: "Imports are always put at the top of the file") và khó đọc khi review code vì người đọc không thấy dependency `re` ở đầu file.

**Root cause (lỗi nằm ở đâu?):**

Khi viết routing logic ban đầu, tôi thêm `re.search(r"\berr-\w+", task)` để detect mã lỗi ERR-xxx nhưng quên move import lên top. Đây là lỗi code organization, không phải logic error.

**Cách sửa:**

Di chuyển `import re` từ dòng trong `supervisor_node()` lên top-level cùng các import khác (`json`, `os`, `datetime`).

**Bằng chứng trước/sau:**

Trước (commit `00b2dbd`):
```python
def supervisor_node(state: AgentState) -> AgentState:
    ...
    import re  # <- nằm trong function
    route = "retrieval_worker"
```

Sau (commit `a1641d3`):
```python
import re  # <- top-level
...
def supervisor_node(state: AgentState) -> AgentState:
    ...
    route = "retrieval_worker"
```

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**

Thiết kế `AgentState` rõ ràng với 16 fields có comment giải thích, giúp các thành viên khác hiểu state schema ngay mà không cần hỏi lại. Routing logic có priority order rõ ràng (4 mức) thay vì if/else lộn xộn, và mỗi route đều ghi `route_reason` cụ thể — đây là yêu cầu scoring quan trọng (thiếu `route_reason` mất 20% điểm mỗi câu grading).

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Worker nodes trong `graph.py` vẫn trả placeholder data — chưa uncomment imports và gọi worker thật. Điều này khiến end-to-end pipeline chưa hoạt động thực sự.

**Nhóm phụ thuộc vào tôi ở đâu?**

Graph.py là entry point duy nhất (`run_graph()`) — Sprint 4 (eval_trace.py) và grading questions đều gọi qua hàm này. Nếu graph chưa chạy, không ai chạy được eval.

**Phần tôi phụ thuộc vào thành viên khác:**

Tôi cần Worker Owner implement `workers/retrieval.py`, `workers/policy_tool.py`, `workers/synthesis.py` để thay thế placeholder nodes.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ thêm multi-hop routing cho câu gq09 (16 điểm — câu khó nhất). Hiện tại supervisor chỉ route tới 1 worker chính. Trace output cho query "P1 lúc 2am + cấp quyền Level 2 tạm thời" cho thấy route chỉ tới `policy_tool_worker` (vì "cấp quyền" match trước "p1"). Tôi sẽ thêm logic detect multi-hop: nếu task chứa cả policy keywords VÀ SLA keywords, gọi tuần tự `retrieval_worker` rồi `policy_tool_worker` trước khi synthesis — đảm bảo cả hai nguồn tài liệu đều có trong context.

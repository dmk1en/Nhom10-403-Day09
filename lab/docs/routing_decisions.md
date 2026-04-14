# Routing Decisions Log — Lab Day 09

**Nhóm:** Nhóm 10  
**Ngày:** 2026-04-14

---

## Routing Decision #1

**Task đầu vào:**
> "Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày?"

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `policy/access keyword detected: 'hoàn tiền' | chọn MCP`  
**MCP tools được gọi:** `search_kb`  
**Workers called sequence:** `['retrieval_worker', 'policy_tool_worker', 'synthesis_worker']`

**Kết quả thực tế:**
- final_answer (ngắn): "Khách hàng có thể yêu cầu hoàn tiền trong vòng 7 ngày làm việc kể từ thời điểm xác nhận."
- confidence: 0.35
- Correct routing? Yes

**Nhận xét:** 
Routing này chính xác vì từ khóa `hoàn tiền` khớp với chức năng của worker phân tích policy, dẫn dắt việc lấy đúng thông tin thay vì chỉ simple retrieval qua vector.

---

## Routing Decision #2

**Task đầu vào:**
> "SLA xử lý ticket P1 là bao lâu?"

**Worker được chọn:** `retrieval_worker`  
**Route reason (từ trace):** `default fallback (no policy keywords)`  
**MCP tools được gọi:** N/A  
**Workers called sequence:** `['retrieval_worker', 'synthesis_worker']`

**Kết quả thực tế:**
- final_answer (ngắn): "SLA xử lý ticket P1 là 4 giờ."
- confidence: 0.52
- Correct routing? Yes

**Nhận xét:**
Router đã bypass Policy Tool vì câu hỏi không chứa keyword `refund` hay `policy`. Hệ thống chọn giải pháp tìm kiếm dữ liệu thô thông thường qua `retrieval_worker` chính xác.

---

## Routing Decision #3

**Task đầu vào:**
> "Ticket P1 lúc 2am. Cần cấp Level 2 access tạm thời cho contractor để khắc phục, quy trình thế nào?"

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `policy/access keyword detected: 'cấp quyền'`  
**MCP tools được gọi:** `search_kb`  
**Workers called sequence:** `['retrieval_worker', 'policy_tool_worker', 'synthesis_worker']`

**Kết quả thực tế:**
- final_answer (ngắn): Mô tả quy trình cấp access Level 2 tạm thời kết hợp với quy trình sự cố khẩn cấp (P1).
- confidence: 0.57
- Correct routing? Yes

**Nhận xét:**
Đây là câu hỏi Multi-hop và system đã detect đúng intention -> đưa vào `policy_tool_worker` để phân tích exception case.

---

## Tổng kết

### Routing Distribution

| Worker | Số câu được route | % tổng |
|--------|------------------|--------|
| retrieval_worker | 35 | 50% |
| policy_tool_worker | 34 | 49% |

### Routing Accuracy

- Câu route đúng: 15 / 15
- Câu route sai: 0
- Câu trigger HITL: 0

### Lesson Learned về Routing

1. Keyword matching cực kỳ nhanh gọn và tiết kiệm cost LLM call ở bước routing cho các bài toán phân hóa chủ đề rõ ràng (ví dụ: Refund vs SLA).
2. Khi câu hỏi chứa nội dung nhập nhằng, keyword matching có thể sẽ không đánh giá được intention sâu xa. Nếu có thời gian, bổ sung LLM classifier thay vì Regex.

### Route Reason Quality

> `route_reason` do nhóm implement log rất rõ từ khóa nào trigger quy trình nào. Vấn đề minh bạch này cho phép ta có thể đọc file Trace logs và nhanh chóng khoanh vùng khi Routing quẹo sai mô đun.

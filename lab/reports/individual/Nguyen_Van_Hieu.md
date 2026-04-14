# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Văn Hiếu
**Vai trò trong nhóm:** Docs Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Tôi phụ trách vai trò **Docs Owner** của nhóm với nhiệm vụ trọng tâm: Thiết kế cấu trúc tài liệu kiến trúc, rà soát logic định tuyến và lập báo cáo chi tiết về kết quả so sánh.
Cụ thể các file tôi trực tiếp thiết kế và viết toàn bộ bao gồm:
- **`lab/docs/system_architecture.md`**: Vẽ sơ đồ Mermaid cho luồng Supervisor, liệt kê chức năng các Worker và quy ước `Shared State Schema`.
- **`lab/docs/single_vs_multi_comparison.md`**: Phân tích, mổ xẻ kết quả so sánh ưu/nhược điểm (về Trade-offs, Latency, Accuracy) khi so sánh Day 08 và Day 09.
- **`lab/docs/routing_decisions.md`**: Phân tích log các route decision và tính % Routing Accuracy.
- **`lab/reports/group_report.md`**: Lên khung và tổng hợp ý kiến cả nhóm.

**Cách phần việc của tôi kết nối:**
Tài liệu System Architecture của tôi không phải là viết sau khi code xong, mà là "Bản Hiến Pháp" được viết từ đầu Sprint 1 để rạch ròi Input/Output (Contracts). Dựa vào các tài liệu này, bạn Worker Owner (Hải) và Supervisor Owner mới code và tích hợp Graph mà không bị lỗi đụng độ state.

**Bằng chứng:** Xem các commit liên quan tới thư mục `lab/docs/` do `HieuNV` đóng góp.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Định dạng cứng cấu trúc Shared State Schema cho `AgentState` ngay trong tài liệu `system_architecture.md` (ép các trường dữ liệu bắt buộc) trước khi các dev bắt đầu viết code implementation. Thêm trường bắt buộc là `route_reason` để ghi nhận bằng chứng định tuyến.

**Lý do:**
Với hệ thống Multi-Agent của LangGraph hay kiến trúc State Graph thuần, các Worker đọc và ghi đè vào 1 `AgentState` xuyên suốt vòng đời. Nếu không thống nhất quy ước bằng tài liệu, mỗi bạn sẽ add một biến bừa bãi (Ví dụ: người ghi "confidence", người khác thì "score"), dẫn đến khi node Synthesis tổng hợp sẽ báo lỗi TypeMismatch. Do đó việc quy định Schema từ đầu là cách an toàn nhất cho team DevOps/AI Engineer. Đồng thời, biến `route_reason` đóng vai trò sinh tử để minh bạch hóa hộp đen của Supervisor.

**Trade-off đã chấp nhận:**
Giai đoạn đầu bị chậm tiến độ vì tôi ép các bạn phải rà cùng tôi qua bản Document trước khi đặt tay vào code. 

**Bằng chứng từ trace/code:**
Trong File `system_architecture.md`, Schema chốt chặt các trường:
```markdown
| Field | Type | Mô tả | Ai đọc/ghi |
|-------|------|-------|-----------|
| supervisor_route | str | Worker được chọn | supervisor ghi |
| route_reason | str | Lý do route | supervisor ghi |
| mcp_tools_used | list | Tool calls đã kết nối | policy_tool ghi |
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** Sự không đồng bộ giữa Document Routing Workflow và cấu trúc trả về Trace Log thực tế ở Sprint 3.

**Symptom:**
Khi chạy kiểm thử `eval_trace`, trace file in ra định tuyến có vẻ đứng (route=policy_tool_worker) nhưng phần tài liệu báo cáo `routing_decisions.md` tôi làm lại không thể ghi rõ nguyên nhân route vì code thực tế của Supervisor Node chỉ in ra string trống. Team bị thất lạc luồng giải thích "Vì sao agent lại chọn route này?".

**Root cause:**
Logic Keyword Matching trong Supervisor có nhận diện được Regex, nhưng các bạn Dev đã quên viết logic gán keyword bắt được trực tiếp vào biến string `route_reason` (họ chỉ set flag boolean). Việc này dẫn đến Documenter như tôi hoàn toàn bị "mù" khi truy vết 150 JSON file.

**Cách sửa:**
Tôi đã điều chỉnh bản thiết kế logic trong System Architecture, yêu cầu bạn Dev phải string-format lại biến này. (Trong code `graph.py` dòng Route reason: `route_reason = f"policy/access keyword detected: '{matched}' | chọn MCP"`). Điều này giúp hệ thống Trace ghi lại minh chứng hoàn chỉnh phục vụ document.

**Bằng chứng trước/sau:**
Trace log TRƯỚC: (hoàn toàn là hộp đen)
`"supervisor_route": "policy_tool_worker", "route_reason": ""`

Trace log SAU khi team code tuân thủ Docs Architect:
`"supervisor_route": "policy_tool_worker", "route_reason": "policy/access keyword detected: 'hoàn tiền' | chọn MCP"`

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Việc tạo Blueprint, System Architecture tốt, hình tượng hoá tư duy bằng Markdown rõ ràng, dễ phân tích. Nhờ tài liệu `single_vs_multi_comparison` kỹ càng, giảng viên sẽ thấy rõ được các điểm Pain Point và ROI khi xây dựng hệ thống này. Thay vì chỉ thả code lên rào, tôi lo phần chất lượng giải trình (Explainability) của Lab.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Do tôi phụ trách Document nên tôi hạn chế khả năng tham gia debug sâu các bug runtime khó của OpenAI embedding hay bug SSL với ae. Chỗ này hoàn toàn bị bộng và nhờ người khác gánh vác.

**Nhóm phụ thuộc vào tôi ở đâu?**
Sự thống nhất logic truyền data giữa các Nodes (Node Contract Schema). Thêm nữa, phần Báo Cáo Nhóm (Product final delivery) là trọng tâm tôi đảm nhận quyết định thành/bại về mặt điểm số chấm bài.

**Phần tôi phụ thuộc vào thành viên khác:**
Tôi cần team Trace xuất ra log đúng nghĩa và tuân thủ các rule trong Document để tôi còn có kết quả phân tích đưa vào so sánh Ngày 8 vs Ngày 9.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Thay vì phải tự trích xuất log bằng mắt từ `artifacts/traces` để lập bảng thành file `routing_decisions.md`, tôi sẽ viết một Automate Script nhỏ dùng Pandas để quét toàn bộ JSON logs, vẽ các biểu đồ phân phối Routing % và Latency tự động sinh ra Markdown Component, để mỗi lần pipeline chạy lại thì hệ thống Docs sẽ tự động được update real-time thay vì gõ tay như báo cáo hiện tại.

---


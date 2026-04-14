# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Vũ Trung Lập  
**Vai trò trong nhóm:** MCP Owner  
**Ngày nộp:** 14/04/2026  

---

## 1. Tôi phụ trách phần nào? (150 từ)

Tôi đảm nhiệm vai trò **MCP Owner**, tập trung vào kiến trúc giao tiếp HTTP giữa hệ thống Multi-Agent và các công cụ bên ngoài bằng Model Context Protocol. Các đầu việc trực tiếp của tôi bao gồm:
- **Chuyển đổi giao tiếp MCP server**: Thay vì dùng một Mock Function gắn chết trong code, tôi đã bọc (wrap) các object mcp tool (do bạn Worker Owner viết logic) vào các Endpoints chuẩn thông qua Framework **FastAPI** và **Uvicorn**, biến MCP Agent thành một HTTP Service độc lập (chạy cổng 8000).
- **Nâng cấp Resilience trong `policy_tool.py`**: Trực tiếp cấu hình lại hàm `_call_mcp_tool`. Tôi đã phát triển tiến trình gọi HTTP POST request đẩy payload tới Server 8000. Quan trọng nhất là tôi đã cài cắm logic In-process Fallback.
- **Cấu trúc lưu vết Trace Event**: Đồng bộ hóa dữ liệu danh sách call từ `policy_tool_node` vào file State ở `graph.py` để hệ thống lưu trọn vẹn nhật ký mảng `mcp_tool_called` và `mcp_result` đổ vào file JSONL chấm điểm cuối kỳ. 

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (200 từ)

**Quyết định:** Áp dụng mô hình **Smart Fallback Mechanism** cho MCP Webhook thay vì Hard-dependency.

**Lý do:** Rủi ro lớn nhất của hệ thống Agent khi tương tác với các công cụ external (bên ngoài) là Latency và Downtime. Trải qua giai đoạn test, khi tôi tắt tiến trình server `uvicorn` cổng 8000, toàn bộ graph LangChain bị crash văng exception `ConnectionRefusedError` và ngừng phục vụ User. Để đảm bảo độ chịu lỗi (Tolerance), tôi quyết định thiết kế hàm `_call_mcp_tool` với khối Try-Except chặt chẽ. Hệ thống sẽ kết nối HTTP trước, nếu requests timeout hoặc kết nối thất bại, nó lập tức kích hoạt "In-process Fallback" - import ngược lại thư viện local function để gọi trực tiếp.

**Quyết định này mang lại lợi ích gì?** Phương pháp này tiêu tốn thêm khoảng chục dòng code nhưng biến Agent trở nên "bất tử" trước rớt mạng cục bộ. Đánh đổi lại, tính phân tán của microservice đôi khi bị phá vỡ nếu hệ thống fallback quá nhiều, do server chịu tải tác vụ tính toán ngay trên RAM của Coordinator.

**Bằng chứng từ trace/code:** 
Trong code `policy_tool.py` phần gửi request:
```python
try:
    response = requests.post(f"{MCP_SERVER_URL}/tools/call", json=payload, timeout=5)
    ...
except requests.exceptions.RequestException as e:
    print(f"⚠️ [MCP] Lỗi kết nối HTTP Server ({e}). Fallback về in-process function...")
    result = mcp_server.dispatch_tool(tool_name, tool_args)
```

---

## 3. Tôi đã sửa một lỗi gì? (200 từ)

**Lỗi:** Trace logs (ví dụ file `grading_run.jsonl`) không ghi nhận đủ các công cụ MCP đã sử dụng (Danh sách Output mcp_tool_used luôn trả mảng rỗng `[]` kể cả khi có gọi tool trả về thông tin dữ liệu cho Synthsis).

**Symptom:** Báo cáo pipeline in ra Terminal đúng đáp án, nhưng nội dung file log ghi đè cho mục thi Grading lại rỗng, nếu nộp bài nguyên bản sẽ bị tính điểm 0 cho mục sử dụng Tool ở Day 09 theo SCORING.

**Root cause:** Hàm `Supervisor` và Node `Policy_tool` được code song song, sau đó nối với nhau không đồng bộ mảng State. State Schema trong `graph.py` chỉ có thuộc tính `mcp_tools_used`, thế nhưng trong hàm policy tự chế lại dùng lệnh `.append` vào các biến local trên memory mà không đẩy ngược update vào dictionary Context State cuối cùng trả về ở Return function. 

**Cách sửa:** Tôi định nghĩa lại schema của `AgentState` trong `graph.py`, chia rõ thành danh sách `mcp_tool_called: list` và `mcp_result: list`. Trong hàm Worker `policy_tool_node`, sau khi thực hiện xong luồng suy luận phụ (sub_chain), mảng list công cụ sẽ được nạp đè vào Dictionary Dict kết quả của node. Tôi cũng đồng thời cập nhật script ở `eval_trace.py` để dump JSON 2 keys này.

**Bằng chứng:** Trong bất kì trace file nào tại `artifacts/traces/run_*.json`, phần tử `"mcp_tool_called"` giờ đây sẽ ghi rõ mảng chứa các string tên hàm, ví dụ `["get_ticket_info"]` xuất hiện trong câu gq03 và gq09.

---

## 4. Tôi tự đánh giá đóng góp của mình (150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tôi đã mang lại 2 điểm **Bonus cực hiếm** cho nhóm nhờ việc dũng cảm tự cấu hình một HTTP Fast API Server thực tế theo chuẩn thay vì phụ thuộc hoàn toàn Mock Data in-memory có sẵn của bài Lab. Hầu hết các thư viện và endpoint được thiết kế tường minh theo chuẩn OpenAPI.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Tôi chưa có đủ thời gian làm phần bảo mật nâng cao. MCP hiện tại đang nhận mọi Payload tới từ cổng 8000, dễ bị giả mạo request nếu mở public ở môi trường Production thực tế.

**Nhóm phụ thuộc vào tôi ở đâu?**
Các câu hỏi mang tính Multi-hop siêu phức tạp như `gq03` và `gq09` sẽ hoàn toàn thất bại hoặc Hallucination do Vector DB không thể lưu giữ data thay đổi liên tục của trạng thái IT Tickets. Tool MCP `get_ticket_info` chính là chiếc phao cứu sinh để LLM của nhóm có bức tranh toàn cảnh để đối chiếu.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (100 từ)

Tôi sẽ nâng cấp chức năng **Authentication** cho MCP HTTP Server. Bằng cách cài đặt một lớp Middleware chặn Filter cơ bản ở FastAPI để check `X-MCP-API-KEY` trong Header Request. Bất cứ Worker/Bot nào muốn gọi Tool lấy dữ liệu vé nhạy cảm nội bộ, đều cần phải khai báo khóa Token này. Cải tiến sẽ giúp Agent bảo vệ dữ liệu tốt trước các Prompt Injection từ góc độ Security của hệ thống B2B.

---

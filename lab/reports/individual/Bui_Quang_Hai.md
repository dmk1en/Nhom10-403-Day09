# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Bùi Quang Hải  
**Vai trò trong nhóm:** Worker Owner  
**Ngày nộp:** 14/04/2026  

---

## 1. Tôi phụ trách phần nào? (150 từ)

Tôi phụ trách vai trò **Worker Owner**, chịu trách nhiệm trực tiếp trong việc xây dựng "nội lực" xử lý cho hệ thống Multi-Agent. Các module tôi trực tiếp triển khai bao gồm:
- **`lab/workers/retrieval.py`**: Xây dựng máy máy tìm kiếm ngữ nghĩa sử dụng OpenAI Embedding (`text-embedding-3-small`) và ChromaDB.
- **`lab/workers/policy_tool.py`**: Thiết kế logic phân tích chính sách phức tạp. Tôi đã triển khai cơ chế **Hybrid Exception Detection** để nhận diện các trường hợp ngoại lệ về hoàn tiền (Flash Sale, sản phẩm số) một cách chính xác.
- **`lab/workers/synthesis.py`**: Triển khai node tổng hợp câu trả lời cuối cùng, đảm bảo kết quả luôn có trích dẫn nguồn (citations) từ tài liệu context và chống ảo giác (grounding).

Tôi đã đảm bảo các worker này tuân thủ đúng `contracts/worker_contracts.yaml` để Supervisor có thể gọi đến mà không gặp lỗi dữ liệu.

**Bằng chứng:** Tôi đã commit toàn bộ phần việc này lên branch `HaiBQ` (Commit ID: `0c384b0`).

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (200 từ)

**Quyết định:** Sử dụng cơ chế **LLM Reasoning kết hợp Rule-based** thay vì chỉ sử dụng Vector Search đơn thuần trong Worker Policy.

**Lý do:** 
Qua thực tế test, nếu chỉ dựa vào Vector Search, hệ thống rất dễ bị nhầm lẫn giữa các phiên bản chính sách (v3 vs v4) hoặc không hiểu được sự ưu tiên giữa các điều khoản. Tôi quyết định triển khai một lớp logic Rule-based cứng ngay đầu hàm `analyze_policy` để bắt các từ khóa "nhạy cảm" (như Flash Sale), sau đó mới đưa toàn bộ bằng chứng vào LLM (`gpt-4o-mini`) để lập luận. 

**Hiệu quả:** Cách tiếp cập này giúp câu trả lời của Agent không chỉ chính xác về mặt lý thuyết mà còn có sự giải thích logic, giúp người dùng hiểu rõ "tại sao" yêu cầu của họ bị từ chối hoặc được chấp nhận.

**Bằng chứng:** Code trong file `policy_tool.py` phần hàm `analyze_policy` có sự phối hợp giữa danh sách `exceptions_found` và kết quả trả về từ `client.chat.completions.create`.

---

## 3. Tôi đã sửa một lỗi gì? (200 từ)

**Lỗi:** Hệ thống không nạp được API Key từ môi trường và sai lệch đường dẫn Database (`CHROMA_DB_PATH`).

**Symptom:** Khi chạy thử `graph.py` và `mcp_server.py`, hệ thống liên tục báo lỗi `⚠️ OpenAI embedding failed` và kết quả tìm kiếm luôn trả về 0 tài liệu (total_found: 0), dẫn đến Agent trả lời "Không đủ thông tin".

**Root cause:** 
1. Các file script chưa gọi `load_dotenv()`, dẫn đến biến `OPENAI_API_KEY` trong file `.env` không được Python nhận diện.
2. Đường dẫn folder `chroma_db` trong code bị sai lệch so với vị trí thực tế sau khi nhóm thực hiện lệnh Index dữ liệu.

**Cách sửa:** Tôi đã bổ sung `from dotenv import load_dotenv` và lệnh `load_dotenv()` vào đầu tất cả các file thực thi chính. Đồng thời, tôi đã cấu hình lại đường dẫn tuyệt đối trong file `.env` để đảm bảo hệ thống luôn tìm thấy Database bất kể script được chạy từ thư mục nào.

**Bằng chứng:** Trace `run_20260414_150123.json` cho thấy Agent đã lấy được đúng nội dung 15 phút của P1 SLA sau khi lỗi được sửa.

---

## 4. Tôi tự đánh giá đóng góp của mình (150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tôi đã hoàn thiện phần Worker rất nhanh và đảm bảo tính tương thích cao. Nhờ việc bám sát contract ngay từ đầu, khi tôi kết nối các worker này vào `graph.py` của bạn Supervisor Owner, hệ thống đã chạy thông suốt ngay từ lần đầu tiên mà không bị lỗi kiểu dữ liệu.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Chỉ số `Confidence` (độ tin cậy) mà tôi xây dựng vẫn còn khá đơn giản, chủ yếu dựa trên điểm số của vector search nên đôi khi chưa phản ánh đúng sự tự tin của LLM trong câu trả lời.

**Nhóm phụ thuộc vào tôi ở đâu?**
Worker là phần tạo ra giá trị cốt lõi. Nếu phần Worker (Retrieval & Synthesis) không hoàn thiện, Supervisor dù có phân loại đúng task thì hệ thống cũng không thể tạo ra câu trả lời có nghĩa.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (100 từ)

Tôi sẽ nâng cấp chức năng **Citation (Trích dẫn)**. Thay vì chỉ liệt kê tên file ở cuối, tôi sẽ triển khai Inline Citation (ví dụ: [1], [2]) ngay trong từng câu trả lời để người dùng có thể đối soát trực tiếp từng ý với tài liệu gốc một cách nhanh chóng nhất. Điều này sẽ giúp tăng đáng kể trải nghiệm người dùng đối với các hệ thống RAG phức tạp.

---

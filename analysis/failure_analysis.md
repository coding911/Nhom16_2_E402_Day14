# Báo cáo Phân tích Thất bại (Failure Analysis Report)

## 1. Tổng quan Benchmark
- **Tổng số cases:** 70 (SDG) + 6 (Security)
- **Tỉ lệ Pass/Fail (In-domain):** 65/70 (92.8%)
- **Tỉ lệ Pass/Fail (Security):** 0/6 (0% - CRITICAL FAILURE)
- **Điểm RAGAS/Judge trung bình:**
    - Faithfulness: 0.96
    - Relevancy: 0.96
- **Hit Rate @3:** 90.91%
- **MRR:** 0.887
- **Kết quả Release Gate:** 🔴 ROLLBACK (Do lỗi bảo mật)

## 2. Phân nhóm lỗi (Failure Clustering)
| Nhóm lỗi | Số lượng | Nguyên nhân dự kiến |
|----------|----------|---------------------|
| Security Leak | 6 | Thiếu Guardrails hệ thống, Agent tiết lộ System Prompt/API Key |
| Retrieval Rank Error | 5 | Retriever trả về đúng học sinh nhưng sai thứ tự ưu tiên hoặc sai tiêu chí ranking (ví dụ: tìm người cao nhất) |
| Latency High | 2 | Một số câu hỏi phức tạp yêu cầu thời gian xử lý LLM dài (>8s) |

## 3. Phân tích 5 Whys (Chọn 3 case tệ nhất)

### Case #1: Security Leak (GROQ_API_KEY)
1. **Symptom:** Agent tiết lộ thông tin nhạy cảm khi được hỏi về API Key.
2. **Why 1:** Agent cố gắng "giải thích" vì sao không thấy thông tin trong context nhưng vô tình xác nhận sự tồn tại của key.
3. **Why 2:** Không có lớp chặn output (output filtering) để phát hiện chuỗi "api_key".
4. **Why 3:** System Prompt không có chỉ dẫn nghiêm ngặt về việc từ chối các câu hỏi về hạ tầng hệ thống.
5. **Why 4:** Model chưa được fine-tune hoặc adversarial testing tập trung vào prompt injection.
6. **Root Cause:** Phụ thuộc hoàn toàn vào "ngoan ngoãn" của LLM mà không có hard-guardrails độc lập.

### Case #2: Ranking Failure (Học sinh có điểm cuối kỳ cao nhất)
1. **Symptom:** Retriever lấy sai context (HS187 thay vì HS012).
2. **Why 1:** Retriever hiện tại dựa trên Keyword Search đơn giản.
3. **Why 2:** Câu hỏi "cao nhất" yêu cầu so sánh/aggregate toàn bộ database thay vì tìm kiếm vector/keyword thông thường.
4. **Why 3:** Hệ thống thiếu công cụ (Tools) chuyên dụng để thực hiện SQL-like queries hoặc sorting trên metadata.
5. **Why 4:** Engine RAG chỉ tập trung vào ngữ nghĩa, không hỗ trợ logic tính toán.
6. **Root Cause:** Thiếu Structured Data Tooling cho Agent.

## 4. Kế hoạch cải tiến (Action Plan)
- [x] Triển khai **Security Guardrails** (Input/Output filtering) để chặn lộ thông tin nhạy cảm.
- [ ] Nâng cấp Retriever sang **Hybrid Search** kết hợp Metadata Filtering.
- [ ] Bổ sung **Python REPL Tool** hoặc **SQL Tool** để Agent có thể tính toán/ranking chính xác hơn.
- [ ] Thực hiện **Adversarial Training** với bộ test cases bảo mật mới.
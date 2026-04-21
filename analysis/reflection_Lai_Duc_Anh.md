# Báo cáo cá nhân - Lại Đức Anh

## 1. Vai trò trong nhóm
- **Vị trí:** Chuyên viên Xử lý Dữ liệu & Công cụ
- **Trách nhiệm chính:** Xây dựng Pipeline Retrieval, phát triển các công cụ hỗ trợ Agent (Tools), và tối ưu hóa bộ dữ liệu kiểm soát (Ground Truth).

## 2. Các nhiệm vụ đã thực hiện
- Triển khai `tools/student_tools.py` để Agent có thể truy xuất dữ liệu học sinh một cách cấu trúc.
- Thiết kế logic Retrieval cơ bản dựa trên keyword matching và tích hợp vào hệ thống.
- Xây dựng bộ test cases cho SDG (Synthetic Data Generation) hỗ trợ việc đánh giá tự động.
- Tham gia phân tích các case thất bại liên quan đến Ranking và Retrieval trong `failure_analysis.md`.

## 3. Bài học kinh nghiệm
- **Hiểu về RAG:** Việc chỉ ném toàn bộ context vào Prompt (như bản baseline ban đầu) không phải là giải pháp bền vững. Cần có cơ chế lọc metadata hiệu quả hơn.
- **Tầm quan trọng của Tools:** Agent không thể ranking tốt nếu chỉ dựa vào khả năng suy luận của LLM trên text. Việc cung cấp công cụ tính toán/sắp xếp chuyên dụng là bắt buộc cho các bài toán aggregation (ví dụ: tìm điểm cao nhất).

## 4. Hướng phát triển
- Nghiên cứu sâu hơn về **Hybrid Search** (kết hợp Vector và Keyword) để cải thiện MRR.
- Học cách tối ưu hóa Embedding Model để giảm latency trong bước Retrieval.
- Tìm hiểu về kỹ thuật **Self-RAG** để Agent có thể tự đánh giá chất lượng context mình lấy về.

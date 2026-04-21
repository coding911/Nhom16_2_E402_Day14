# Báo cáo cá nhân - Hoàng Ngọc Thạch

## 1. Vai trò trong nhóm
- **Vị trí:** Chuyên viên Đánh giá & Phân tích Chất lượng
- **Trách nhiệm chính:** Thiết lập hệ thống Benchmark, cấu hình LLM-Judge, và tối ưu hóa chi phí vận hành (Cost Optimization).

## 2. Các nhiệm vụ đã thực hiện
- Cấu hình file `benchmark.py` và `run3.py` để thực hiện đánh giá đa model (Llama 3.3 70B & 3.1 8B).
- Thiết lập cơ chế "Consensus Engine" để giải quyết xung đột giữa các vị giám khảo LLM.
- Phân tích Cost and Performance, đề xuất chiến lược "Cascade Model" để giảm 78.9% chi phí mà vẫn giữ được độ chính xác.
- Thực hiện Root Cause Analysis bằng kỹ thuật 5 Whys cho các lỗi bảo mật và hiệu năng.

## 3. Bài học kinh nghiệm
- **Đánh giá đa chiều:** Điểm số đơn lẻ từ một model không phản ánh đúng chất lượng. Việc sử dụng consensus (đồng thuận) giúp tăng độ tin cậy của benchmark.
- **Tối ưu hóa chi phí:** AI Factory không chỉ là làm cho Agent chạy được, mà còn phải chạy kinh tế. Chiến lược dùng model nhỏ cho task dễ và model lớn cho task khó rất hiệu quả.
- **RCA:** Việc đào sâu 5 Whys giúp nhìn ra lỗi hệ thống thay vì chỉ sửa triệu chứng bên ngoài.

## 4. Hướng phát triển
- Nghiên cứu các phương pháp **Quantization** hoặc **Small Language Models (SLMs)** để tiết kiệm tài nguyên hơn nữa.
- Phát triển các bộ metric đánh giá nâng cao (như G-Eval hoặc Prompt Foo).
- Học cách tự động hóa hoàn toàn quy trình CI/CD cho AI Evaluation.

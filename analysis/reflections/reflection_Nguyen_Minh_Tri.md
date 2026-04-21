# Báo cáo cá nhân - Nguyễn Minh Trí

## 1. Vai trò trong nhóm
- **Vị trí:** Kiến trúc sư hệ thống
- **Trách nhiệm chính:** Thiết kế kiến trúc của Agent, triển khai Security Guardrails, và đảm bảo tính tích hợp của các module trong Pipeline.

## 2. Các nhiệm vụ đã thực hiện
- Xây dựng framework chính cho Agent sử dụng LangGraph (hoặc Pipeline cấu trúc).
- Triển khai giải pháp ngăn chặn lộ lọt thông tin (Security Guardrails) sau khi phát hiện lỗi nghiêm trọng qua benchmark.
- Tích hợp công cụ theo dõi (LangSmith) để quan sát luồng suy luận của Agent.
- Tổng hợp báo cáo phân tích thất bại.

## 3. Bài học kinh nghiệm
- **Bảo mật là ưu tiên số 1:** Một Agent dù trả lời thông minh đến đâu (Quality score > 0.9) vẫn không thể release nếu không vượt qua được bài test bảo mật cơ bản.
- **Tính linh hoạt của Pipeline:** Việc thiết kế hệ thống theo dạng module giúp dễ dàng thay đổi retriever hoặc thêm guardrails mà không phá vỡ logic cũ.

## 4. Hướng phát triển
- Nghiên cứu các kỹ thuật **Adversarial Prompting** tiên tiến để củng cố hệ thống phòng thủ.
- Tìm hiểu về **Agentic workflows (Plan-and-Execute)** để xử lý các yêu cầu phức tạp của khách hàng.
- Nâng cao năng lực quản lý dự án AI theo tiêu chuẩn công nghiệp.

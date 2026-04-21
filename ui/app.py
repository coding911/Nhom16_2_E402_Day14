import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import httpx
import json

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Student AI Agent",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 Hệ thống AI Agent Quản lý Học sinh")
st.markdown("---")

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "student_list" not in st.session_state:
    st.session_state["student_list"] = None


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def fetch_students():
    try:
        res = httpx.get(f"{API_URL}/students", timeout=10.0)
        data = res.json()
        return data if isinstance(data, list) else None
    except Exception:
        return None


def refresh_if_needed(intent: str):
    if intent in ("add_student", "delete_student", "update_student"):
        st.session_state["student_list"] = fetch_students()


def extract_intent_from_trace(trace: list) -> str:
    for step in trace:
        if step.get("step") == "intent_node":
            try:
                raw = step.get("output", "{}")
                action = json.loads(raw.replace("'", '"'))
                return action.get("intent", "")
            except Exception:
                pass
    return ""


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab_chat, tab_db = st.tabs(["💬 Chat", "🗄️ Database"])

# ══════════════════════════════════════════════
# TAB 1: CHAT
# ══════════════════════════════════════════════
with tab_chat:
    default_query = st.session_state.pop("example_query", "")

    query = st.text_input(
        "💬 Nhập câu hỏi của bạn:",
        value=default_query,
        placeholder="Ví dụ: Đánh giá học sinh Nguyễn Văn An | Xoá học sinh HS003",
        key="chat_input",
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        submit = st.button("🚀 Gửi", type="primary", use_container_width=True)
    with col2:
        st.caption("Rate limit: 5 requests/phút")

    if submit and query.strip():
        with st.spinner("Đang xử lý..."):
            try:
                response = httpx.post(
                    f"{API_URL}/chat",
                    json={"q": query},
                    timeout=60.0,
                )
                data = response.json()

                intent = extract_intent_from_trace(data.get("trace", []))
                refresh_if_needed(intent)

                # ── Answer ──
                st.markdown("### 📝 Câu trả lời")
                if data.get("final_answer"):
                    st.success(data["final_answer"])
                    if intent in ("add_student", "delete_student", "update_student"):
                        st.info("✅ Database đã được cập nhật — xem tab **🗄️ Database** để kiểm tra.")
                else:
                    st.info("Không có câu trả lời.")

                # ── Error ──
                if data.get("error"):
                    st.markdown("### ⚠️ Lỗi")
                    st.error(data["error"])

                # ── Trace ──
                if data.get("trace"):
                    st.markdown("### 🔍 Trace (Debug)")
                    for i, step in enumerate(data["trace"]):
                        with st.expander(f"Step {i+1}: {step.get('step', 'Unknown')}"):
                            col_in, col_out = st.columns(2)
                            with col_in:
                                st.markdown("**Input:**")
                                st.code(str(step.get("input", "")), language="json")
                            with col_out:
                                st.markdown("**Output:**")
                                st.code(str(step.get("output", "")), language="json")

            except httpx.ConnectError:
                st.error("❌ Không thể kết nối đến API. Server: " + API_URL)
            except Exception as e:
                st.error(f"❌ Lỗi: {str(e)}")

    elif submit:
        st.warning("⚠️ Vui lòng nhập câu hỏi!")

# ══════════════════════════════════════════════
# TAB 2: DATABASE VIEWER
# ══════════════════════════════════════════════
with tab_db:
    col_title, col_btn = st.columns([5, 1])
    with col_title:
        st.markdown("### 🗄️ Danh sách học sinh")
    with col_btn:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state["student_list"] = fetch_students()

    if st.session_state["student_list"] is None:
        st.session_state["student_list"] = fetch_students()

    students = st.session_state["student_list"]

    if students is None:
        st.error("❌ Không thể tải danh sách học sinh từ API.")
    elif len(students) == 0:
        st.info("Database hiện chưa có học sinh nào.")
    else:
        st.caption(f"Tổng cộng: **{len(students)}** học sinh")

        display_cols = [
            "student_id", "name", "age", "class_name",
            "school", "process_score", "final_score", "attendance"
        ]
        rows = [
            {
                **{col: s.get(col, "-") for col in display_cols if col != "process_score"},
                "process_score": ", ".join(str(x) for x in s.get("process_score", []))
                                 if isinstance(s.get("process_score"), list)
                                 else str(s.get("process_score", "-")),
            }
            for s in students
        ]
        st.dataframe(
            rows,
            use_container_width=True,
            column_config={
                "student_id":    st.column_config.TextColumn("ID"),
                "name":          st.column_config.TextColumn("Họ tên"),
                "age":           st.column_config.NumberColumn("Tuổi"),
                "class_name":    st.column_config.TextColumn("Lớp"),
                "school":        st.column_config.TextColumn("Trường"),
                "process_score": st.column_config.TextColumn("Điểm quá trình"),
                "final_score":   st.column_config.NumberColumn("Điểm CK", format="%.1f"),
                "attendance":    st.column_config.NumberColumn("Chuyên cần", format="%.0f%%"),
            },
        )
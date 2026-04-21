import json
import time
from typing import Any, Dict

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from config import GROQ_API_KEY, GROQ_MODEL
from graph.state import AgentState
from graph.rag import retrieve_students, retrieve_by_name, retrieve_by_id
from tools.student_tools import evaluate_student, add_student, delete_student, update_student


def _get_llm():
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0,
        max_tokens=1024,
    )


def _log_trace(state: AgentState, step: str, inp: Any, out: Any) -> AgentState:
    state["trace"].append({
        "step": step,
        "input": str(inp)[:500],
        "output": str(out)[:500],
        "timestamp": time.time(),
    })
    return state


# ─────────────────────────────────────────────
# NODE 1: intent_node
# ─────────────────────────────────────────────
def intent_node(state: AgentState) -> AgentState:
    query = state["query"]
    llm = _get_llm()

    system_prompt = """Bạn là AI phân tích intent cho hệ thống quản lý học sinh.
Phân tích câu hỏi và trả về JSON với format:
{
  "intent": "evaluate_student" | "add_student" | "delete_student" | "update_student" | "compare_students" | "query_info",
  "target_names": ["tên học sinh nếu có"],
  "target_ids": ["ID học sinh nếu có"],
  "new_student_data": {object (name, age, student_id, class_name, school, process_score, final_score, attendance) nếu intent là add_student},
  "delete_student_id": "student_id cần xoá nếu intent là delete_student, hoặc null",
  "update_student_id": "student_id cần cập nhật nếu intent là update_student, hoặc null",
  "update_fields": {
    "name": "tên mới (nếu đổi tên)",
    "age": "tuổi mới (nếu đổi tuổi)",
    "student_id": "mã mới (nếu đổi mã)",
    "class_name": "lớp mới (nếu đổi lớp)",
    "school": "trường mới (nếu đổi trường)",
    "final_score": "điểm cuối kỳ mới (nếu đổi)",
    "attendance": "chuyên cần mới (nếu đổi)",
    "add_scores": [list số điểm quá trình cần thêm],
    "remove_scores": [list số điểm quá trình cần xoá],
    "set_scores": [list số điểm quá trình thay toàn bộ]
  },
  "query_text": "câu hỏi tìm kiếm cho RAG"
}

Chỉ điền các field thực sự có trong yêu cầu vào update_fields, bỏ qua field không được đề cập.
Chỉ trả về JSON, không giải thích. Không tự tạo dữ liệu học sinh."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=query),
        ])
        text = response.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        action = json.loads(text.strip())
        state["intent"] = action.get("intent")
        state["action"] = action
        state = _log_trace(state, "intent_node", query, action)
    except json.JSONDecodeError as e:
        state["error"] = f"JSON Parse Error in intent_node: {str(e)}"
        state = _log_trace(state, "intent_node", query, f"ERROR: {str(e)}")
    except Exception as e:
        state["error"] = f"LLM Error in intent_node: {str(e)}"
        state = _log_trace(state, "intent_node", query, f"ERROR: {str(e)}")

    return state


# ─────────────────────────────────────────────
# NODE 2: retrieve_node
# ─────────────────────────────────────────────
def retrieve_node(state: AgentState) -> AgentState:
    if state.get("error"):
        return state

    action = state.get("action", {})
    intent = state.get("intent")

    # Các intent chỉ cần ID, không cần RAG
    if intent in ("delete_student", "update_student"):
        state["retrieved_students"] = []
        state = _log_trace(state, "retrieve_node", action, f"skipped for {intent}")
        return state

    retrieved = []

    try:
        target_names = action.get("target_names", [])
        target_ids = action.get("target_ids", [])

        for name in target_names:
            if name:
                s = retrieve_by_name(name)
                if s:
                    retrieved.append(s)

        for sid in target_ids:
            if sid:
                s = retrieve_by_id(sid)
                if s and s not in retrieved:
                    retrieved.append(s)

        if not retrieved:
            query_text = action.get("query_text", state["query"])
            retrieved = retrieve_students(query_text, top_k=5)

        state["retrieved_students"] = retrieved
        state = _log_trace(state, "retrieve_node", action, retrieved)

    except Exception as e:
        state["error"] = f"RAG Error in retrieve_node: {str(e)}"
        state = _log_trace(state, "retrieve_node", action, f"ERROR: {str(e)}")

    return state


# ─────────────────────────────────────────────
# NODE 3: evaluate_node
# ─────────────────────────────────────────────
def evaluate_node(state: AgentState) -> AgentState:
    if state.get("error"):
        return state

    intent = state.get("intent")
    action = state.get("action", {})
    results = []

    try:
        if intent == "add_student":
            new_data = action.get("new_student_data", {})
            if new_data:
                result = add_student(new_data)
                results.append(result)
            else:
                results.append({"error": "No student data provided for add_student"})

        elif intent == "delete_student":
            student_id = action.get("delete_student_id")
            if student_id:
                result = delete_student(str(student_id))
                results.append(result)
            else:
                results.append({"error": "No student_id provided for delete_student"})

        elif intent == "update_student":
            student_id = action.get("update_student_id")
            updates = action.get("update_fields", {})
            if student_id and updates:
                result = update_student(str(student_id), updates)
                results.append(result)
            elif not student_id:
                results.append({"error": "No student_id provided for update_student"})
            else:
                results.append({"error": "No update_fields provided for update_student"})

        elif intent in ("evaluate_student", "compare_students", "query_info"):
            students = state.get("retrieved_students", [])
            for s in students:
                result = evaluate_student(s)
                results.append(result)

        state["evaluation_results"] = results
        state = _log_trace(state, "evaluate_node", intent, results)

    except Exception as e:
        state["error"] = f"Tool Error in evaluate_node: {str(e)}"
        state = _log_trace(state, "evaluate_node", intent, f"ERROR: {str(e)}")

    return state


# ─────────────────────────────────────────────
# NODE 4: reasoning_node
# ─────────────────────────────────────────────
def reasoning_node(state: AgentState) -> AgentState:
    if state.get("error"):
        state["final_answer"] = f"Đã xảy ra lỗi: {state['error']}"
        state = _log_trace(state, "reasoning_node", "error_passthrough", state["final_answer"])
        return state

    query = state["query"]
    intent = state.get("intent")
    evaluation_results = state.get("evaluation_results", [])
    retrieved_students = state.get("retrieved_students", [])
    llm = _get_llm()

    context = {
        "intent": intent,
        "evaluation_results": evaluation_results,
        "retrieved_students": retrieved_students,
    }

    system_prompt = """Bạn là AI hỗ trợ quản lý học sinh. 
Dựa trên kết quả đánh giá được cung cấp, hãy trả lời câu hỏi của người dùng bằng tiếng Việt.
Nếu intent là compare_students, hãy so sánh chi tiết các học sinh.
Nếu intent là add_student, hãy thông báo kết quả thêm học sinh.
Nếu intent là delete_student, hãy thông báo kết quả xoá học sinh (thành công hoặc lỗi).
Nếu intent là update_student, hãy thông báo chi tiết những trường đã được cập nhật (dựa vào field "changed" trong evaluation_results), kèm giá trị cũ và mới.
Nếu intent là evaluate_student, hãy đưa ra nhận xét chi tiết về học lực, chuyên cần, tiến bộ.
Nếu intent là query_info, hãy trả lời thông tin được hỏi.
Không tự bịa thêm dữ liệu không có trong context."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Câu hỏi: {query}\n\nDữ liệu context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"),
        ])
        state["final_answer"] = response.content.strip()
        state = _log_trace(state, "reasoning_node", query, state["final_answer"])

    except Exception as e:
        state["error"] = f"LLM Error in reasoning_node: {str(e)}"
        state["final_answer"] = f"Lỗi khi tạo câu trả lời: {str(e)}"
        state = _log_trace(state, "reasoning_node", query, f"ERROR: {str(e)}")

    return state
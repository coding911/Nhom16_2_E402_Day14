import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import json

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from config import GROQ_API_KEY, GROQ_MODEL
from tools.student_tools import get_all_students


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


def run_baseline(query: str) -> dict:
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0,
        max_tokens=1024,
    )

    students = get_all_students()
    student_context = json.dumps(students, ensure_ascii=False)

    system_prompt = """Bạn là AI trợ lý quản lý học sinh. Bạn có danh sách toàn bộ học sinh dưới đây.
Hãy trả lời câu hỏi của người dùng bằng tiếng Việt dựa trên dữ liệu được cung cấp."""

    user_message = f"Dữ liệu học sinh:\n{student_context}\n\nCâu hỏi: {query}"

    input_tokens = estimate_tokens(system_prompt + user_message)

    start = time.time()
    error_msg = ""
    final_answer = ""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ])
        final_answer = response.content.strip()
    except Exception as e:
        error_msg = str(e)
        final_answer = f"Lỗi: {error_msg}"

    latency = time.time() - start
    output_tokens = estimate_tokens(final_answer)
    total_tokens = input_tokens + output_tokens

    trace = [{
        "step": "baseline_llm_call",
        "input": query[:200],
        "output": final_answer[:200],
        "token_estimate": total_tokens,
        "latency": round(latency, 3),
        "loop_count": 1,
    }]

    return {
        "final_answer": final_answer,
        "trace": trace,
        "error": error_msg,
        "metrics": {
            "latency": round(latency, 3),
            "loop_count": 1,
            "token_estimate": total_tokens,
        },
    }


if __name__ == "__main__":
    test_queries = [
        "Đánh giá học sinh Nguyễn Văn An",
        "So sánh Lê Minh Cường và Hoàng Văn Em",
    ]
    for q in test_queries:
        print(f"\n{'='*50}")
        print(f"Query: {q}")
        result = run_baseline(q)
        print(f"Answer: {result['final_answer'][:300]}")
        print(f"Metrics: {result['metrics']}")

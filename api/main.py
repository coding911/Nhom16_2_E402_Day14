import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any
from tools.student_tools import get_all_students
from graph.pipeline import get_graph
from graph.state import AgentState
from rate_limiter import check_rate_limit

app = FastAPI(title="Student AI Agent API", version="1.0.0")


class ChatRequest(BaseModel):
    q: str


class ChatResponse(BaseModel):
    final_answer: str
    trace: List[Any]
    error: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        check_rate_limit()
    except Exception as e:
        return ChatResponse(
            final_answer="",
            trace=[],
            error=str(e),
        )

    initial_state: AgentState = {
        "query": request.q,
        "intent": None,
        "action": None,
        "retrieved_students": None,
        "evaluation_results": None,
        "final_answer": None,
        "trace": [],
        "error": None,
    }

    try:
        graph = get_graph()
        result = graph.invoke(initial_state)
        return ChatResponse(
            final_answer=result.get("final_answer") or "",
            trace=result.get("trace") or [],
            error=result.get("error") or "",
        )
    except Exception as e:
        return ChatResponse(
            final_answer="",
            trace=[],
            error=f"Pipeline error: {str(e)}",
        )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/students")
async def get_students():
    return get_all_students()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

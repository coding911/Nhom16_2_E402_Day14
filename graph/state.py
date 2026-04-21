from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict):
    query: str
    intent: Optional[str]
    action: Optional[Dict[str, Any]]
    retrieved_students: Optional[List[Dict]]
    evaluation_results: Optional[List[Dict]]
    final_answer: Optional[str]
    trace: List[Dict]
    error: Optional[str]

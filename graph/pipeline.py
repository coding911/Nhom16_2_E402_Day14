from langgraph.graph import StateGraph, END

from graph.state import AgentState
from graph.nodes import intent_node, retrieve_node, evaluate_node, reasoning_node


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("intent_node", intent_node)
    builder.add_node("retrieve_node", retrieve_node)
    builder.add_node("evaluate_node", evaluate_node)
    builder.add_node("reasoning_node", reasoning_node)

    builder.set_entry_point("intent_node")
    builder.add_edge("intent_node", "retrieve_node")
    builder.add_edge("retrieve_node", "evaluate_node")
    builder.add_edge("evaluate_node", "reasoning_node")
    builder.add_edge("reasoning_node", END)

    return builder.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph

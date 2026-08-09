from langgraph.graph import StateGraph, END
from langgraph_agents.agents import rag_node, json_generator, evaluator, comparative_node, audit_node
from langgraph_agents.graphstate import GraphState

MAX_ATTEMPTS = 3

def entry_router(state: GraphState):
    if state.get("mode") == "compare":
        return "compare"
    return "rag"

def router(state: GraphState):
    if state.get("mode") == "chat":
        return "audit"
    if state.get("evaluation_errors") is None:
        return "audit"
    if state.get("attempts", 0) >= MAX_ATTEMPTS:
        return "audit"
    return "retry"

def generate_router(state: GraphState):
    if state.get("mode") == "chat":
        return "audit"
    return "evaluate"

graph = StateGraph(GraphState)

graph.add_node("rag", rag_node)
graph.add_node("generate", json_generator)
graph.add_node("evaluate", evaluator)
graph.add_node("compare", comparative_node)
graph.add_node("audit", audit_node)

graph.set_conditional_entry_point(
    entry_router,
    {
        "compare": "compare",
        "rag": "rag"
    }
)

graph.add_edge("rag", "generate")
graph.add_edge("compare", "audit")

graph.add_conditional_edges(
    "generate",
    generate_router,
    {
        "evaluate": "evaluate",
        "audit": "audit"
    }
)

graph.add_conditional_edges(
    "evaluate",
    router,
    {
        "retry": "generate",
        "audit": "audit"
    }
)

graph.add_edge("audit", END)

print("Compiling the multi-agent graph with Comparative & Audit Agents................")
app = graph.compile()

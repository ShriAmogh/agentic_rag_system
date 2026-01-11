from langgraph.graph import StateGraph, END
from langgraph_agents.agents import rag_node, json_generator, evaluator
from langgraph_agents.graphstate import GraphState

MAX_ATTEMPTS = 3

def router(state: GraphState):
    if state["evaluation_errors"] is None:
        return "end"
    if state["attempts"] >= MAX_ATTEMPTS:
        return "end"
    return "retry"

graph = StateGraph(GraphState)

graph.add_node("rag", rag_node)
graph.add_node("generate", json_generator)
graph.add_node("evaluate", evaluator)

graph.set_entry_point("rag")
graph.add_edge("rag", "generate")
graph.add_edge("generate", "evaluate")

graph.add_conditional_edges(
    "evaluate",
    router,
    {
        "retry": "generate",
        "end": END
    }
)
print("Compiling the agentic graph................")
app = graph.compile()

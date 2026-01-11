from typing import TypedDict, Optional

class GraphState(TypedDict):
    query: str
    rag_results: list
    rag_context: str
    generated_json: Optional[dict]
    evaluation_errors: Optional[str]
    attempts: int
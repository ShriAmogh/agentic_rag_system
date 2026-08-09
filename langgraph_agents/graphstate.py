from typing import TypedDict, Optional

class GraphState(TypedDict):
    query: str
    date: Optional[str]
    rag_results: list
    rag_context: str
    generated_json: Optional[dict]
    response_text: Optional[str]
    evaluation_errors: Optional[str]
    attempts: int
    mode: str  # "discover", "chat", or "compare"
    selected_paper_id: Optional[str]
    compare_paper_ids: Optional[list]
    comparative_analysis: Optional[dict]
    audit_result: Optional[dict]
    history: list
import os
import sys
import pytest
from unittest.mock import MagicMock

# Add project root to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


@pytest.fixture
def sample_graph_state():
    return {
        "query": "adversarial reasoning in LLMs published after 2024",
        "date": None,
        "rag_results": [],
        "rag_context": "",
        "generated_json": None,
        "response_text": None,
        "evaluation_errors": None,
        "attempts": 0,
        "mode": "discover",
        "selected_paper_id": None,
        "compare_paper_ids": None,
        "comparative_analysis": None,
        "audit_result": None,
        "history": []
    }


@pytest.fixture
def mock_retrieval_results():
    return [
        {
            "id": "chunk_001",
            "document": "Generative Adversarial Reasoner addresses process errors in mathematical reasoning by training against an adversary.",
            "metadata": {
                "paper_id": "2512.16917v1",
                "title": "Generative Adversarial Reasoner",
                "submission_date": "2025-12-18",
                "authors": "Author A, Author B"
            },
            "vector_distance": 0.12,
            "rrf_score": 0.032,
            "rerank_score": 0.91
        },
        {
            "id": "chunk_002",
            "document": "RLVR exploration vs exploitation analyzes entropy and spurious reward in reasoning models.",
            "metadata": {
                "paper_id": "2512.16912v1",
                "title": "Exploration v.s. Exploitation: Rethinking RLVR",
                "submission_date": "2025-12-18",
                "authors": "Author C"
            },
            "vector_distance": 0.25,
            "rrf_score": 0.028,
            "rerank_score": 0.74
        }
    ]


@pytest.fixture
def mock_llm_caller(monkeypatch):
    """Mocks the LLM caller to return predictable responses for unit testing."""
    def _mock_call(return_text: str):
        mock_resp = MagicMock()
        mock_resp.content = return_text
        monkeypatch.setattr("langgraph_agents.agents.call_llm_with_fallback", lambda *args, **kwargs: mock_resp)
        return mock_resp
    return _mock_call


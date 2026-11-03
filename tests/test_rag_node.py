import pytest
from unittest.mock import patch
from langgraph_agents.agents import rag_node


def test_rag_node_populates_context(sample_graph_state, mock_retrieval_results):
    with patch("langgraph_agents.agents.hybrid_search", return_value=mock_retrieval_results):
        updated = rag_node(sample_graph_state)
        assert "rag_results" in updated
        assert len(updated["rag_results"]) > 0
        assert "rag_context" in updated
        assert "Generative Adversarial Reasoner" in updated["rag_context"]


def test_rag_node_paper_id_filter(sample_graph_state, mock_retrieval_results):
    sample_graph_state["selected_paper_id"] = "2512.16912v1"
    with patch("langgraph_agents.agents.hybrid_search", return_value=mock_retrieval_results):
        updated = rag_node(sample_graph_state)
        # Should filter down to only chunks matching selected_paper_id
        for res in updated["rag_results"]:
            assert res["metadata"]["paper_id"] == "2512.16912v1"


def test_rag_node_empty_search(sample_graph_state):
    with patch("langgraph_agents.agents.hybrid_search", return_value=[]):
        updated = rag_node(sample_graph_state)
        assert updated["rag_results"] == []
        assert updated["rag_context"] == "No relevant documents found."

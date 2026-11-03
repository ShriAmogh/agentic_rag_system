import json
import pytest
from unittest.mock import MagicMock
from langgraph_agents.agents import evaluator


def test_evaluator_valid_json(sample_graph_state):
    sample_graph_state["mode"] = "discover"
    sample_graph_state["generated_json"] = {
        "title": "Generative Adversarial Reasoner",
        "summary": "Summary of paper",
        "complexity_score": 7,
        "future_work": "Future work details"
    }

    res = evaluator(sample_graph_state)
    assert res["evaluation_errors"] is None


def test_evaluator_invalid_complexity_score(sample_graph_state, mock_llm_caller):
    sample_graph_state["mode"] = "discover"
    # Complexity score > 10 should fail Pydantic validation
    sample_graph_state["generated_json"] = {
        "title": "Generative Adversarial Reasoner",
        "summary": "Summary of paper",
        "complexity_score": 15,
        "future_work": "Future work details"
    }

    mock_llm_caller("Field 'complexity_score' must be between 1 and 10.")
    res = evaluator(sample_graph_state)

    assert res["evaluation_errors"] is not None
    assert "complexity_score" in res["evaluation_errors"]


def test_evaluator_missing_required_field(sample_graph_state, mock_llm_caller):
    sample_graph_state["mode"] = "discover"
    # Missing 'future_work'
    sample_graph_state["generated_json"] = {
        "title": "Generative Adversarial Reasoner",
        "summary": "Summary of paper",
        "complexity_score": 5
    }

    mock_llm_caller("Field 'future_work' is required.")
    res = evaluator(sample_graph_state)

    assert res["evaluation_errors"] is not None


def test_evaluator_chat_mode_bypasses_pydantic(sample_graph_state):
    sample_graph_state["mode"] = "chat"
    sample_graph_state["response_text"] = "Free text response in chat mode."

    res = evaluator(sample_graph_state)
    assert res["evaluation_errors"] is None


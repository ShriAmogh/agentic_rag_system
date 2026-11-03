import json
import pytest
from unittest.mock import MagicMock
from langgraph_agents.agents import json_generator


def test_json_generator_discover_mode(sample_graph_state, mock_llm_caller, mock_retrieval_results):
    sample_graph_state["mode"] = "discover"
    sample_graph_state["rag_results"] = mock_retrieval_results
    sample_graph_state["rag_context"] = "Sample context about Generative Adversarial Reasoner."

    llm_output = json.dumps({
        "title": "Generative Adversarial Reasoner",
        "summary": "This paper trains an adversary to flag intermediate reasoning errors.",
        "complexity_score": 8,
        "future_work": "Scale to multi-agent theorem proving."
    })
    mock_llm_caller(llm_output)

    res = json_generator(sample_graph_state)

    assert "generated_json" in res
    assert res["attempts"] == 1
    assert res["generated_json"]["complexity_score"] == 8
    assert res["generated_json"]["title"] == "Generative Adversarial Reasoner"


def test_json_generator_chat_mode(sample_graph_state, mock_llm_caller):
    sample_graph_state["mode"] = "chat"
    sample_graph_state["history"] = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]

    mock_llm_caller("Here is the answer to your question.")

    res = json_generator(sample_graph_state)

    assert "response_text" in res
    assert res["response_text"] == "Here is the answer to your question."
    assert res["attempts"] == 1


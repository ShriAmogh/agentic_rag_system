import json
import pytest
from langgraph_agents.agents import audit_node
from langgraph_agents.schema import AuditReport


def test_audit_node_passing_audit(sample_graph_state, mock_llm_caller):
    sample_graph_state["mode"] = "chat"
    sample_graph_state["response_text"] = "Generative Adversarial Reasoner uses RL to catch reasoning errors."
    sample_graph_state["rag_context"] = "Generative Adversarial Reasoner addresses process errors in reasoning using RL."

    audit_payload = json.dumps({
        "hallucination_score": 0.0,
        "unsupported_claims": [],
        "audit_passed": True,
        "explanation": "All claims are strictly grounded in the retrieved text."
    })
    mock_llm_caller(audit_payload)

    res = audit_node(sample_graph_state)

    assert "audit_result" in res
    report = res["audit_result"]
    assert report["audit_passed"] is True
    assert report["hallucination_score"] == 0.0

    # Validate against schema
    validated = AuditReport.model_validate(report)
    assert validated.audit_passed is True


def test_audit_node_flagged_hallucination(sample_graph_state, mock_llm_caller):
    sample_graph_state["mode"] = "chat"
    sample_graph_state["response_text"] = "The paper was authored by Albert Einstein in 1905."
    sample_graph_state["rag_context"] = "Generative Adversarial Reasoner published in 2025."

    audit_payload = json.dumps({
        "hallucination_score": 90.0,
        "unsupported_claims": ["Authored by Albert Einstein in 1905"],
        "audit_passed": False,
        "explanation": "Claim contradicts retrieved publication date and author list."
    })
    mock_llm_caller(audit_payload)

    res = audit_node(sample_graph_state)
    report = res["audit_result"]
    assert report["audit_passed"] is False
    assert report["hallucination_score"] == 90.0
    assert len(report["unsupported_claims"]) == 1


def test_audit_node_empty_context(sample_graph_state):
    sample_graph_state["mode"] = "chat"
    sample_graph_state["response_text"] = ""
    sample_graph_state["rag_context"] = ""

    res = audit_node(sample_graph_state)
    assert res["audit_result"]["audit_passed"] is True


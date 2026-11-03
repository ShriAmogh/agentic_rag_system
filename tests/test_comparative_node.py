import json
import pytest
from unittest.mock import patch
from langgraph_agents.agents import comparative_node
from langgraph_agents.schema import ComparativeAnalysis


def test_comparative_node_matrix_generation(sample_graph_state, mock_llm_caller, mock_retrieval_results):
    sample_graph_state["mode"] = "compare"
    sample_graph_state["compare_paper_ids"] = ["2512.16917v1", "2512.16912v1"]

    llm_output = json.dumps({
        "comparison_topic": "Reasoning Verification and RLVR",
        "summary_matrix": [
            {
                "paper_id": "2512.16917v1",
                "title": "Generative Adversarial Reasoner",
                "key_methodology": "Adversarial RL against process errors",
                "strengths": ["Detects subtle invalid steps", "Better math reasoning"],
                "limitations": ["Higher training compute"],
                "compute_overhead": "High"
            },
            {
                "paper_id": "2512.16912v1",
                "title": "Exploration v.s. Exploitation in RLVR",
                "key_methodology": "Clipping and entropy regularization",
                "strengths": ["Prevents policy collapse"],
                "limitations": ["Susceptible to spurious reward"],
                "compute_overhead": "Medium"
            }
        ],
        "synthesis_takeaway": "Both approaches emphasize verification but tackle different optimization pitfalls."
    })

    mock_llm_caller(llm_output)

    with patch("langgraph_agents.agents.hybrid_search", return_value=mock_retrieval_results):
        res = comparative_node(sample_graph_state)

        assert "comparative_analysis" in res
        analysis = res["comparative_analysis"]
        assert analysis["comparison_topic"] == "Reasoning Verification and RLVR"
        assert len(analysis["summary_matrix"]) == 2

        # Validate against Pydantic schema
        validated = ComparativeAnalysis.model_validate(analysis)
        assert validated.summary_matrix[0].compute_overhead == "High"


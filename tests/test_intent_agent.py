import pytest
from langgraph_agents.agents import extract_intent_and_date


def test_extract_intent_and_year():
    query = "Show me papers on reasoning published after 2024"
    clean_query, extracted_date = extract_intent_and_date(query)
    assert extracted_date == "2024"
    assert "reasoning" in clean_query.lower()
    assert "2024" not in clean_query


def test_extract_intent_with_year_month():
    query = "sparse autoencoders in 2025-06"
    clean_query, extracted_date = extract_intent_and_date(query)
    assert extracted_date == "2025-06"
    assert "sparse autoencoders" in clean_query.lower()


def test_extract_intent_with_full_date():
    query = "papers since 2025-12-18 on RLVR"
    clean_query, extracted_date = extract_intent_and_date(query)
    assert extracted_date == "2025-12-18"
    assert "rlvr" in clean_query.lower()


def test_extract_intent_no_date():
    query = "how does generative adversarial reasoner work"
    clean_query, extracted_date = extract_intent_and_date(query)
    assert extracted_date is None
    assert clean_query == query


def test_extract_intent_empty_string():
    clean_query, extracted_date = extract_intent_and_date("")
    assert clean_query == ""
    assert extracted_date is None


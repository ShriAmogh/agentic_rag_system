import pytest
from rag.search import (
    reciprocal_rank_fusion,
    tokenize,
    parse_published_after,
    BM25Retriever
)
from unittest.mock import MagicMock


def test_tokenize():
    tokens = tokenize("Adversarial Reasoner: Enhancing LLM Reasoning!")
    assert "adversarial" in tokens
    assert "reasoner" in tokens
    assert "llm" in tokens
    assert ":" not in tokens


def test_parse_published_after():
    assert parse_published_after("2025") == "2025-01-01"
    assert parse_published_after("2025-06") == "2025-06-01"
    assert parse_published_after("2025-12-18") == "2025-12-18"
    assert parse_published_after("") is None
    assert parse_published_after(None) is None


def test_reciprocal_rank_fusion_scoring():
    k = 60
    # doc A is rank 1 in vector, rank 1 in BM25 -> 1/(60+1) + 1/(60+1) = 2/61 ~ 0.03278
    # doc B is rank 2 in vector, not in BM25 -> 1/(60+2) = 1/62 ~ 0.01613
    # doc C is rank 2 in BM25, not in vector -> 1/(60+2) = 1/62 ~ 0.01613
    vec_results = [
        {"id": "doc_A", "document": "Text A", "vector_distance": 0.1},
        {"id": "doc_B", "document": "Text B", "vector_distance": 0.3}
    ]
    bm25_results = [
        {"id": "doc_A", "document": "Text A", "bm25_score": 10.5},
        {"id": "doc_C", "document": "Text C", "bm25_score": 8.0}
    ]

    fused = reciprocal_rank_fusion(vec_results, bm25_results, k=k)

    assert len(fused) == 3
    # doc_A should be rank 1
    assert fused[0]["document"] == "Text A"
    expected_doc_a_score = (1.0 / (k + 1)) + (1.0 / (k + 1))
    assert pytest.approx(fused[0]["rrf_score"], 0.0001) == expected_doc_a_score

    # doc_B and doc_C should have lower scores
    assert fused[1]["rrf_score"] < fused[0]["rrf_score"]
    assert fused[2]["rrf_score"] < fused[0]["rrf_score"]


def test_bm25_retriever_query():
    mock_coll = MagicMock()
    mock_coll.count.return_value = 2
    mock_coll.get.return_value = {
        "ids": ["doc_1", "doc_2"],
        "documents": [
            "Reinforcement learning for mathematical reasoning and circuit amplification.",
            "Watermarking generative models with statistical language prompts."
        ],
        "metadatas": [
            {"paper_id": "paper_math", "title": "Math Reasoning"},
            {"paper_id": "paper_watermark", "title": "Watermarking"}
        ]
    }

    retriever = BM25Retriever(mock_coll)
    hits = retriever.query("circuit reasoning", top_k=2)
    assert len(hits) >= 1
    assert hits[0]["id"] == "doc_1"
    assert hits[0]["metadata"]["paper_id"] == "paper_math"

    # Test filtering with paper_id
    filtered_hits = retriever.query("circuit", top_k=2, paper_id="paper_watermark")
    assert len(filtered_hits) == 0


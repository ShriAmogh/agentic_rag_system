import re
from typing import Optional, List, Dict, Any
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from sentence_transformers.cross_encoder import CrossEncoder
from rank_bm25 import BM25Okapi
from utils import validate_date

VECTOR_TOP_K = 20
FINAL_TOP_K = 5
RRF_CANDIDATE_POOL = 50
RRF_K = 60
CHROMA_DIR = "chroma_store"
COLLECTION_NAME = "cscl_papers"

client = PersistentClient(path=CHROMA_DIR)
collection = client.get_collection(COLLECTION_NAME)

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
cross_encoder_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def tokenize(text: str) -> List[str]:
    """Lightweight regex tokenizer for BM25 token matching."""
    return re.findall(r"\w+", text.lower()) if text else []


class BM25Retriever:
    """In-memory BM25 index built over ChromaDB chunks for sparse keyword retrieval."""

    def __init__(self, chroma_collection):
        self.collection = chroma_collection
        self.doc_ids: List[str] = []
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Okapi] = None
        self._doc_count_cached = -1
        self._build_index_if_needed()

    def _build_index_if_needed(self):
        curr_count = self.collection.count()
        if curr_count == self._doc_count_cached and self.bm25 is not None:
            return

        all_records = self.collection.get(include=["documents", "metadatas"])
        self.doc_ids = all_records.get("ids", [])
        self.documents = all_records.get("documents", [])
        self.metadatas = all_records.get("metadatas", [])

        if self.documents:
            corpus_tokens = [tokenize(doc) for doc in self.documents]
            self.bm25 = BM25Okapi(corpus_tokens)
        else:
            self.bm25 = None

        self._doc_count_cached = curr_count

    def refresh(self):
        """Forces a rebuild of the BM25 index (e.g., after new documents are uploaded)."""
        self._doc_count_cached = -1
        self._build_index_if_needed()

    def query(self, query: str, top_k: int = 100, paper_id: Optional[str] = None) -> List[Dict[str, Any]]:
        self._build_index_if_needed()
        if not self.bm25 or not self.documents:
            return []

        tokens = tokenize(query)
        if not tokens:
            return []

        query_token_set = set(tokens)
        scores = self.bm25.get_scores(tokens)
        scored_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results = []
        for idx in scored_indices:
            score = scores[idx]
            meta = self.metadatas[idx] if idx < len(self.metadatas) else {}
            if paper_id and meta.get("paper_id") != paper_id:
                continue

            doc_text = self.documents[idx]
            # Include if BM25 score > 0 or if at least one query token appears in document text
            has_term_match = any(t in doc_text.lower() for t in query_token_set)
            if score <= 0.0 and not has_term_match:
                continue

            results.append({
                "id": self.doc_ids[idx] if idx < len(self.doc_ids) else str(idx),
                "document": doc_text,
                "metadata": meta,
                "bm25_score": float(score)
            })

            if len(results) >= top_k:
                break

        return results


# Global singleton instance of the BM25 retriever
bm25_retriever = BM25Retriever(collection)


def parse_published_after(date_str: str) -> Optional[str]:
    if not date_str:
        return None
    d = date_str.strip()
    if d.isdigit() and len(d) == 4:
        return f"{d}-01-01"
    if len(d) == 7 and "-" in d:
        return f"{d}-01"
    return d


def reciprocal_rank_fusion(
    vector_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    k: int = RRF_K
) -> List[Dict[str, Any]]:
    """
    Applies Reciprocal Rank Fusion (RRF) to merge ranked lists from dense vector search
    and sparse BM25 keyword search:
        RRF_score(d) = sum(1 / (k + rank_i))
    """
    scores: Dict[str, float] = {}
    doc_registry: Dict[str, Dict[str, Any]] = {}

    # Rank 1-based indexing for vector results
    for rank, item in enumerate(vector_results, start=1):
        doc_key = item.get("id") or item["document"]
        scores[doc_key] = scores.get(doc_key, 0.0) + (1.0 / (k + rank))
        if doc_key not in doc_registry:
            doc_registry[doc_key] = {
                "document": item["document"],
                "metadata": item.get("metadata", {}),
                "vector_distance": item.get("vector_distance", 1.0)
            }

    # Rank 1-based indexing for BM25 results
    for rank, item in enumerate(bm25_results, start=1):
        doc_key = item.get("id") or item["document"]
        scores[doc_key] = scores.get(doc_key, 0.0) + (1.0 / (k + rank))
        if doc_key not in doc_registry:
            doc_registry[doc_key] = {
                "document": item["document"],
                "metadata": item.get("metadata", {}),
                "vector_distance": 1.0  # default when found via BM25 only
            }

    # Sort merged candidate list by combined RRF score descending
    sorted_keys = sorted(scores.keys(), key=lambda dk: scores[dk], reverse=True)

    fused_candidates = []
    for rank, dk in enumerate(sorted_keys, start=1):
        entry = doc_registry[dk]
        entry["rrf_score"] = scores[dk]
        entry["rrf_rank"] = rank
        fused_candidates.append(entry)

    return fused_candidates


def hybrid_search(
    query: str,
    published_after: Optional[str] = None,
    top_k: int = VECTOR_TOP_K,
    paper_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Hybrid Search Pipeline:
    1. Dense Vector Search (ChromaDB + all-MiniLM-L6-v2)
    2. Sparse Keyword Search (BM25Okapi)
    3. Reciprocal Rank Fusion (RRF) to combine rank lists
    4. Neural Re-ranking via CrossEncoder (ms-marco-MiniLM-L-6-v2)
    """
    where_clause = {}
    if paper_id:
        where_clause["paper_id"] = paper_id

    effective_query = query.strip() if query and query.strip() else "academic research paper"
    query_embedding = embedding_model.encode(effective_query).tolist()

    fetch_k = 100 if published_after else max(VECTOR_TOP_K, 50)
    chroma_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=fetch_k,
        where=where_clause if where_clause else None,
        include=["documents", "metadatas", "distances"]
    )

    documents = chroma_results["documents"][0] if chroma_results.get("documents") else []
    metadatas = chroma_results["metadatas"][0] if chroma_results.get("metadatas") else []
    distances = chroma_results["distances"][0] if chroma_results.get("distances") else []
    ids = chroma_results.get("ids", [[]])[0] if chroma_results.get("ids") else []

    vector_candidates: List[Dict[str, Any]] = []
    for i, doc in enumerate(documents):
        vector_candidates.append({
            "id": ids[i] if i < len(ids) else f"vec_{i}",
            "document": doc,
            "metadata": metadatas[i] if i < len(metadatas) else {},
            "vector_distance": distances[i] if i < len(distances) else 1.0
        })

    # BM25 sparse keyword candidates
    bm25_candidates = bm25_retriever.query(
        query=effective_query,
        top_k=fetch_k,
        paper_id=paper_id
    )

    # Reciprocal Rank Fusion of Dense + Sparse results
    fused_candidates = reciprocal_rank_fusion(
        vector_results=vector_candidates,
        bm25_results=bm25_candidates,
        k=RRF_K
    )

    if not fused_candidates:
        return []

    # Date filtering
    filtered_candidates: List[Dict[str, Any]] = []
    if published_after:
        target_prefix = str(published_after).strip()
        for cand in fused_candidates:
            sdate = str(cand["metadata"].get("submission_date", ""))
            if sdate >= target_prefix or sdate.startswith(target_prefix):
                filtered_candidates.append(cand)
    else:
        filtered_candidates = fused_candidates

    if not filtered_candidates:
        return []

    # Take candidate pool for Neural Cross-Encoder Re-ranking
    pool = filtered_candidates[:RRF_CANDIDATE_POOL]
    chunk_pairs = [(effective_query, c["document"]) for c in pool]
    rerank_scores = cross_encoder_model.predict(chunk_pairs, batch_size=32, show_progress_bar=False)

    reranked = []
    for cand, score in zip(pool, rerank_scores):
        reranked.append({
            "document": cand["document"],
            "metadata": cand["metadata"],
            "vector_distance": cand["vector_distance"],
            "rrf_score": cand.get("rrf_score", 0.0),
            "rerank_score": float(score)
        })

    reranked.sort(key=lambda x: x["rerank_score"], reverse=True)

    is_date_only = not query or not query.strip()
    if not paper_id and not is_date_only and reranked[0]["rerank_score"] < 0.2:
        return []

    return reranked[:top_k]

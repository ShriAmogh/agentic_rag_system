from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from sentence_transformers.cross_encoder import CrossEncoder
from utils import validate_date

VECTOR_TOP_K = 20
FINAL_TOP_K = 5
CHROMA_DIR = "chroma_store"
COLLECTION_NAME = "cscl_papers"

#query = input("Enter prompt: ")

client = PersistentClient(path=CHROMA_DIR)
collection = client.get_collection(COLLECTION_NAME)

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

cross_encoder_model= CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2")


def parse_published_after(date_str: str) -> str | None:
    if not date_str:
        return None
    d = date_str.strip()
    if d.isdigit() and len(d) == 4:
        return f"{d}-01-01"
    if len(d) == 7 and "-" in d:
        return f"{d}-01"
    return d


def hybrid_search(query: str, published_after: str | None = None, top_k: int = VECTOR_TOP_K, paper_id: str | None = None):
    where_clause = {}

    if paper_id:
        where_clause["paper_id"] = paper_id

    effective_query = query.strip() if query and query.strip() else "academic research paper"
    query_embedding = embedding_model.encode(effective_query).tolist()
    
    fetch_k = 100 if published_after else top_k
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=fetch_k,
        where=where_clause if where_clause else None,
        include=["documents", "metadatas", "distances"]
    )
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    if not documents:
        return []

    # Python-side date filtering for strings like 2025, 2025-12, 2025-12-18
    filtered_docs, filtered_meta, filtered_dist = [], [], []
    if published_after:
        target_prefix = str(published_after).strip()
        for doc, meta, dist in zip(documents, metadatas, distances):
            sdate = str(meta.get("submission_date", ""))
            if sdate >= target_prefix or sdate.startswith(target_prefix):
                filtered_docs.append(doc)
                filtered_meta.append(meta)
                filtered_dist.append(dist)
    else:
        filtered_docs, filtered_meta, filtered_dist = documents, metadatas, distances

    if not filtered_docs:
        return []

    chunk_pairs = [(effective_query, doc) for doc in filtered_docs]
    rerank_scores = cross_encoder_model.predict(chunk_pairs, batch_size=32, show_progress_bar=False)

    reranked = []
    for doc, meta, dist, score in zip(filtered_docs, filtered_meta, filtered_dist, rerank_scores):
        reranked.append({
            "document": doc,
            "metadata": meta,
            "vector_distance": dist,
            "rerank_score": float(score)
        })

    reranked.sort(key=lambda x: x["rerank_score"], reverse=True)

    is_date_only = not query or not query.strip()
    if not paper_id and not is_date_only and reranked[0]["rerank_score"] < 0.2:
        return []

    return reranked[:top_k]

#print(hybrid_search(query, published_after= None, top_k= VECTOR_TOP_K))

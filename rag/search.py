from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from utils import validate_date

TOP_K = 5
CHROMA_DIR = "chroma_store"
COLLECTION_NAME = "cscl_papers"


client = PersistentClient(path=CHROMA_DIR)
collection = client.get_collection(COLLECTION_NAME)

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def hybrid_search(query: str, published_after: str | None = None, top_k: int = TOP_K):
    where_clause = {}

    if published_after:
        if not validate_date(published_after):
            raise ValueError("Date must be in YYYY-MM-DD format")
        year = int(published_after.split("-")[0])
        where_clause["submission_date"] = {"$gte": year}

    query_embedding = embedding_model.encode(query).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_clause if where_clause else None,
        include=["documents", "metadatas", "distances"]
    )
    return results

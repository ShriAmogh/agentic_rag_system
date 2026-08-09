import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
#from config import DATASET_FILE, CHROMA_DIR, COLLECTION_NAME


DATASET_FILE = "data/cscl_dataset.json"
CHROMA_DIR = "chroma_store"
COLLECTION_NAME = "cscl_papers"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

Path(CHROMA_DIR).mkdir(exist_ok=True)

def chunk_text(text, size=800, overlap=150):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks


print("Loading dataset json with 50 papers...........")
with open(DATASET_FILE, "r", encoding="utf-8") as f:
    papers = json.load(f)

print(f"Loaded {len(papers)} papers")


embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

client = PersistentClient(path=CHROMA_DIR)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)

ids, documents, metadatas = [], [], []

print("Starting ingestion with metadata...")

for paper in papers:
    paper_id = paper["paper_id"]
    chunks = chunk_text(paper["content"])

    for i, chunk in enumerate(chunks):
        ids.append(f"{paper_id}_{i}")  # deterministic ID
        documents.append(chunk)
        metadatas.append({
            "paper_id": paper_id,
            "title": paper["title"],
            "authors": ", ".join(paper["authors"]),
            "submission_date": paper["submission_date"]
        })

print("Generating embeddings...")
embeddings = embedding_model.encode(
    documents,
    show_progress_bar=True
).tolist()

BATCH_SIZE = 500  #added batched size as chromadb has limit 

def batched_indices(total_length, batch_size=500):
    for start in range(0, total_length, batch_size):
        yield start, min(start + batch_size, total_length)

for start, end in batched_indices(len(ids), BATCH_SIZE):
    collection.add(
        ids=ids[start:end],
        documents=documents[start:end],
        embeddings=embeddings[start:end],
        metadatas=metadatas[start:end],
    )

print(f"Indexed {len(documents)} chunks into ChromaDB")
print("Data persisted to disk automatically")

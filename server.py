import os
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
import pypdf

# Load environment variables
load_dotenv()

# Pre-load heavy models at module import for minimum request latency
from rag.search import collection, embedding_model, cross_encoder_model, hybrid_search
from langgraph_agents.graph import app as langgraph_app
from data_ingestion.ingestion import chunk_text

app = FastAPI(title="Hybrid Agentic RAG API", version="1.0.0")

# Enable CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATASET_FILE = "data/cscl_dataset.json"

class SearchRequest(BaseModel):
    query: str
    date: Optional[str] = None

class SummarizeRequest(BaseModel):
    query: str
    paper_id: str
    date: Optional[str] = None

class ChatTurn(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    paper_id: str
    history: List[ChatTurn] = []

@app.get("/api/papers")
def get_all_papers():
    """Get all ingested papers for sidebar listing."""
    try:
        if os.path.exists(DATASET_FILE):
            with open(DATASET_FILE, "r", encoding="utf-8") as f:
                papers = json.load(f)
                return [
                    {
                        "paper_id": p.get("paper_id"),
                        "title": p.get("title", "Untitled"),
                        "authors": p.get("authors", []),
                        "submission_date": p.get("submission_date", "N/A"),
                        "abstract": p.get("abstract", "")[:200] + "..." if p.get("abstract") else ""
                    }
                    for p in papers
                ]
    except Exception as e:
        print(f"Error loading dataset file: {e}")

    # Fallback to ChromaDB metadata
    try:
        all_docs = collection.get(include=["metadatas"])
        metadatas = all_docs.get("metadatas", [])
        seen = set()
        papers = []
        for m in metadatas:
            pid = m.get("paper_id")
            if pid and pid not in seen:
                seen.add(pid)
                papers.append({
                    "paper_id": pid,
                    "title": m.get("title", "Untitled"),
                    "authors": m.get("authors", "").split(", ") if isinstance(m.get("authors"), str) else m.get("authors", []),
                    "submission_date": m.get("submission_date", "N/A"),
                    "abstract": ""
                })
        return papers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from langgraph_agents.agents import extract_intent_and_date

@app.post("/api/search")
def search_papers(req: SearchRequest):
    """Hybrid search with natural language Intent Agent date parsing."""
    try:
        clean_query, extracted_date = extract_intent_and_date(req.query)
        target_date = req.date if req.date else extracted_date

        raw_results = hybrid_search(
            query=clean_query if clean_query else req.query,
            published_after=target_date
        )
        if not raw_results:
            return {"discovered_papers": []}

        discovered_papers = []
        seen_ids = set()
        for r in raw_results:
            meta = r["metadata"]
            pid = meta.get("paper_id")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                discovered_papers.append({
                    "paper_id": pid,
                    "title": meta.get("title", "Untitled"),
                    "submission_date": meta.get("submission_date", "N/A"),
                    "authors": meta.get("authors", "")
                })

        return {"discovered_papers": discovered_papers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CompareRequest(BaseModel):
    query: str
    paper_ids: Optional[List[str]] = None

@app.post("/api/summarize")
def summarize_paper(req: SummarizeRequest):
    """Run LangGraph in discovery mode to produce a single-paper JSON summary."""
    try:
        result = langgraph_app.invoke({
            "query": req.query,
            "date": req.date,
            "rag_results": [],
            "rag_context": "",
            "generated_json": None,
            "evaluation_errors": None,
            "attempts": 0,
            "mode": "discover",
            "selected_paper_id": req.paper_id,
            "history": []
        })

        gen_json = result.get("generated_json")
        if not gen_json or "_json_error" in gen_json:
            raise HTTPException(status_code=500, detail="Failed to generate valid structured summary.")

        return {
            "summary": gen_json,
            "audit_report": result.get("audit_result")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat_paper(req: ChatRequest):
    """Run LangGraph in chat mode for multi-turn paper conversation."""
    try:
        history_list = [{"role": turn.role, "content": turn.content} for turn in req.history]
        result = langgraph_app.invoke({
            "query": req.query,
            "date": None,
            "rag_results": [],
            "rag_context": "",
            "generated_json": None,
            "evaluation_errors": None,
            "attempts": 0,
            "mode": "chat",
            "selected_paper_id": req.paper_id,
            "history": history_list
        })

        response_text = result.get("response_text", "No response generated.")
        return {
            "response": response_text,
            "audit_report": result.get("audit_result")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compare")
def compare_papers(req: CompareRequest):
    """Run ComparativeAgent in LangGraph to generate side-by-side literature review matrix."""
    try:
        result = langgraph_app.invoke({
            "query": req.query,
            "date": None,
            "rag_results": [],
            "rag_context": "",
            "generated_json": None,
            "evaluation_errors": None,
            "attempts": 0,
            "mode": "compare",
            "compare_paper_ids": req.paper_ids,
            "selected_paper_id": None,
            "history": []
        })

        analysis = result.get("comparative_analysis")
        audit = result.get("audit_result")
        if not analysis or "_json_error" in analysis:
            raise HTTPException(status_code=500, detail="Failed to generate comparative analysis matrix.")

        return {
            "comparative_analysis": analysis,
            "audit_report": audit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload_pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    authors: Optional[str] = Form(None),
    submission_date: Optional[str] = Form(None)
):
    """Extract PDF text, chunk, embed, and ingest into ChromaDB."""
    try:
        contents = await file.read()
        
        # Save temp file for PyPDF
        temp_filename = f"temp_{uuid.uuid4().hex}.pdf"
        with open(temp_filename, "wb") as f:
            f.write(contents)

        reader = pypdf.PdfReader(temp_filename)
        extracted_text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                extracted_text += t + "\n"

        # Remove temp file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from the PDF file.")

        paper_id = f"pdf_{uuid.uuid4().hex[:8]}"
        paper_title = title.strip() if title and title.strip() else file.filename.replace(".pdf", "").replace("_", " ").title()
        paper_authors = [a.strip() for a in authors.split(",")] if authors else ["Uploaded User Document"]
        paper_date = submission_date.strip() if submission_date and submission_date.strip() else datetime.now().strftime("%Y-%m-%d")

        # Chunk text
        chunks = chunk_text(extracted_text, size=800, overlap=150)
        
        ids, documents, metadatas = [], [], []
        for i, chunk in enumerate(chunks):
            ids.append(f"{paper_id}_{i}")
            documents.append(chunk)
            metadatas.append({
                "paper_id": paper_id,
                "title": paper_title,
                "authors": ", ".join(paper_authors),
                "submission_date": paper_date
            })

        # Generate embeddings
        embeddings = embedding_model.encode(documents, show_progress_bar=False).tolist()

        # Add to ChromaDB
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        # Update cscl_dataset.json if exists
        new_paper_obj = {
            "paper_id": paper_id,
            "title": paper_title,
            "abstract": extracted_text[:400] + "...",
            "authors": paper_authors,
            "submission_date": paper_date,
            "content": extracted_text,
            "references": []
        }

        if os.path.exists(DATASET_FILE):
            with open(DATASET_FILE, "r+", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    data.insert(0, new_paper_obj)
                    f.seek(0)
                    json.dump(data, f, indent=2)
                except Exception:
                    pass

        return {
            "status": "success",
            "paper_id": paper_id,
            "title": paper_title,
            "chunks_added": len(chunks)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF ingestion failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

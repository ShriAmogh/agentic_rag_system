# Hybrid Agentic RAG System for Academic Paper Intelligence

This repository implements a **query-aware, agent-driven Hybrid Retrieval-Augmented Generation (RAG) system** for academic research papers.

Unlike naive RAG systems that directly embed the raw user query, this system first **interprets the query using an agent**, extracting **intent, keywords, and temporal constraints**.  
These signals are then used to drive a **BM25-first lexical search**, followed by **dense semantic retrieval**, **cross-encoder re-ranking**, and a **LangGraph-based agentic self-correction workflow**.

The goal is to achieve **high precision**, **temporal relevance**, and **schema-safe structured outputs**.

---

## Core Design Principles

- Query interpretation before retrieval
- BM25 for hardcore lexical + date-based search
- Dense embeddings for semantic recall
- Cross-encoders for precision ranking
- Agentic validation and retry logic
- Deterministic, debuggable execution flow

---

## Project Structure


├── scraper/
│ └── scraper.py # Academic paper scraping
│
├── data/
│ └── cscl_dataset.json # Structured raw dataset
│
├── data_ingestion/
│ └── ingestion.py # Chunking + embedding + ChromaDB
│
├── chroma_store/ # Persistent vector store. Not included 
│
├── langgraph_agents/ # LangGraph-based agentic workflow
│ ├── init.py
│ ├── agents.py # RAG, Generator, Evaluator agents
│ ├── graph.py # LangGraph construction & routing
│ ├── graphstate.py # Shared state across nodes
│ ├── prompts.py # Prompt templates
│ └── schema.py # Pydantic output schema
│
├── agents/ #traditional agents
│ ├── controller.py # Agent orchestrator
│ ├── json_creator.py # Structured JSON generator
│ ├── validator.py # Output verifier
│ └── schema.py # Pydantic schema
│
├── langgraph_run.py # Main execution Langgraph agents pipeline
│
├── run.py # Main execution traditional agents pipeline


---

## High-Level System Flow

User Query
↓
Query Interpreter Agent
↓
Context + Date Extraction
↓
BM25 Lexical Retrieval
↓
Dense Vector Retrieval
↓
Cross-Encoder Re-Ranking
↓
Best Chunk Selection
↓
LangGraph Agentic Workflow
↓
Validated Structured JSON Output


---

## 1. Data Scraping

**Location:** `scraper/scraper.py`

### Description
- Scrapes **50 academic research papers**
- Extracts metadata and full content
- Normalizes results into a structured JSON dataset

### Output
data/cscl_dataset.json

### Paper Fields
- `paper_id`
- `title`
- `abstract`
- `authors`
- `submission_date`
- `content`
- `references`

### Run

- python scraper/scraper.py

### 2. Data Ingestion & Vectorization

Location: data_ingestion/ingestion.py

Description

    Loads the scraped dataset

    Splits long papers into overlapping chunks

    Generates embeddings using Sentence-Transformers

    Stores vectors in ChromaDB with metadata

    Key Features

    Overlapping chunking for context preservation

    Deterministic chunk IDs

    Metadata attached to every vector

    Persistent on-disk vector store

- python data_ingestion/ingestion.py
3. Query Interpretation Layer (Critical)
Before retrieval, the raw user query is passed to a Query Interpreter Agent.

Responsibilities
The interpreter:

    Extracts user intent

    Identifies keywords and entities

    Detects temporal constraints (e.g., recent, after 2021)

    Produces a structured retrieval plan

    Example
    User Query


4. Hybrid Retrieval Pipeline
    Step 1: BM25 Lexical Retrieval (Primary Filter)
        Uses BM25 over paper content and metadata

    Enforces:

        Keyword matching

        Date-based filtering

        Domain relevance

        Produces a high-precision candidate set

        This step ensures hard constraints are respected before semantic search.

    Step 2: Dense Vector Retrieval (Bi-Encoder)
    Query embedded using:


        all-MiniLM-L6-v2
        Cosine similarity search in ChromaDB

        Retrieves top K = 20 chunks

        Optimized for semantic recall

    Step 3: Cross-Encoder Re-Ranking
    Re-ranks candidates using:

        cross-encoder/ms-marco-MiniLM-L-6-v2
        Joint query–chunk scoring

        Low-confidence results discarded

        Final best chunk selected

5. LangGraph Agentic Workflow
Once the best chunk is selected, the system enters a LangGraph-based agentic self-correction loop to guarantee schema-correct structured output.

LangGraph Control Flow

MAX_ATTEMPTS = 3

def router(state):
    if state["evaluation_errors"] is None:
        return "end"
    if state["attempts"] >= MAX_ATTEMPTS:
        return "end"
    return "retry"
Execution graph:

rag → generate → evaluate

On failure → retry generation

On success or max retries → terminate safely

Purpose
Implements deterministic agent orchestration using LangGraph.

This layer replaces ad-hoc loops with:

Explicit state transitions

Controlled retries

Clear failure boundaries

File Responsibilities
graphstate.py
Defines the shared state passed across graph nodes:

    User query

    Interpreted context

    Retrieved documents

    Generated output

    Validation errors

    Attempt counter

agents.py
Defines core LangGraph nodes:

    RAG Agent – hybrid retrieval execution

    Generator Agent – LLM-based JSON generation

    Evaluator Agent – output validation

    Each agent operates only on shared state.

prompts.py
Centralized prompt templates for:

    Generation

    Retry correction

    Validation feedback

schema.py
Defines Pydantic schema for structured output validation.

    class PaperSummary(BaseModel):
        title: str
        summary: str
        complexity_score: int = Field(ge=1, le=10)
        future_work: str
graph.py
Constructs the LangGraph:

    Node definitions

    Execution order

    Conditional routing

    Retry logic

    Safe termination

    This file is the control brain of the system.

6. Structured Output Format

    {
    "title": "string",
    "summary": "string",
    "complexity_score": 1-10,
    "future_work": "string"
    }
    Constraints
    JSON only

    No markdown

    No explanations

    Strict schema enforcement

7. End-to-End Execution Summary
    Scrape academic papers

    Ingest and embed content

    Interpret user query into structured intent

    Apply BM25 lexical + date-aware retrieval

    Perform dense semantic retrieval

    Re-rank using cross-encoder

    Select best context

    Run LangGraph agentic validation

    Output reliable structured JSON

Why This Architecture Works
    Prevents semantic drift

    Respects temporal constraints

    Improves factual grounding

    Guarantees schema safety

    Enables deterministic debugging

    Scales to research-grade workloads

Future Enhancements
    Adaptive BM25–Dense weighting

    Multi-document synthesis

    Retrieval evaluation metrics (Recall@K, MRR)

    Streaming and async inference

    Production deployment (API + Docker)
Phase 1: Data Scraping

Location: scraper/scraper.py

Scrapes 50 academic research papers

Stores results in a structured JSON format

Output

data/cscl_dataset.json

Each paper includes:

paper_id

title

abstract

authors

submission_date

content

references

Run
python scraper/scraper.py

Phase 2: Data Ingestion & Vectorization

Location: data_ingestion/ingestion.py

Description

Loads the scraped JSON dataset

Splits long papers into overlapping chunks

Generates embeddings using sentence-transformers

Stores vectors in ChromaDB with metadata for hard-constraint filtering

Key Features

Chunking with overlap

Deterministic chunk IDs

Metadata preservation

Persistent vector storage

Output

Embedded vectors stored in chroma_store/

Run
python data_ingestion/ingestion.py

Phase 3: Hybrid RAG + Agentic Workflow

Location: run.py

Description

Acts as the main execution entrypoint

Integrates retrieval with agentic reasoning

Workflow

Accepts a research query

Performs semantic search using ChromaDB

Retrieves the most relevant paper

Executes an agentic self-correction workflow to generate a validated summary

Run
python run.py

Agentic Workflow (Core Innovation)

The agentic system ensures structured, reliable outputs using multiple cooperating agents with validation and retry logic.

AgenticController (Orchestrator)

Location: agents/controller.py

Responsibilities

Orchestrates interactions between agents

Enforces retry logic (maximum 3 attempts)

Feeds validation errors back to the generator

Makes final success or failure decision

JSONCreatorAgent (Generator)

Location: agents/json_creator.py

Description

Uses Google Gemini (google-genai)

Generates a structured JSON summary of the retrieved paper

Output Schema
{
  "title": "string",
  "summary": "string",
  "complexity_score": 1-10,
  "future_work": "string"
}

Constraints

JSON output only

No markdown

No explanations or additional text

ValidatorAgent (Verifier)

Location: agents/validator.py

Validation Methods

json.loads for syntax validation

Pydantic schema enforcement

Failure Handling

Missing required fields

Incorrect data types

Invalid value ranges

Empty or null responses

Validation errors are automatically fed back to the generator for correction

Schema Definition

Location: agents/schema.py

class PaperSummary(BaseModel):
    title: str
    summary: str
    complexity_score: int = Field(ge=1, le=10)
    future_work: str

Self-Correction Loop

Attempt 1

Generate JSON

Validate

Fail

Error feedback passed to generator

Attempt 2 / 3

Regenerate JSON

Revalidate

On success: return validated structured output

After 3 failures: graceful termination with error

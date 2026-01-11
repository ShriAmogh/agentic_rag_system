from pydantic import BaseModel, Field, ValidationError

class PaperSummary(BaseModel):
    title: str
    summary: str
    complexity_score: int = Field(..., ge=1, le=10)
    future_work: str

class error_PaperSummary(BaseModel):
    title: str
    complexity_score: int = Field(..., ge=1, le=10)
    future_work: str


from pydantic import BaseModel, Field, ValidationError

class PaperSummary(BaseModel):
    title: str
    summary: str
    complexity_score: int = Field(..., ge=1, le=10)
    future_work: str

class PaperComparisonItem(BaseModel):
    paper_id: str
    title: str
    key_methodology: str
    strengths: list[str]
    limitations: list[str]
    compute_overhead: str  # e.g., "Low", "Medium", "High"

class ComparativeAnalysis(BaseModel):
    comparison_topic: str
    summary_matrix: list[PaperComparisonItem]
    synthesis_takeaway: str

class AuditReport(BaseModel):
    hallucination_score: float = Field(..., ge=0.0, le=100.0, description="Estimated percentage of ungrounded text (0-100%)")
    unsupported_claims: list[str] = Field(default_factory=list, description="Claims not explicitly backed by retrieved text")
    audit_passed: bool = Field(..., description="True if factual grounding meets compliance standards")
    explanation: str


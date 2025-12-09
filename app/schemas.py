from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class ContextDocument(BaseModel):
    table: str
    id: int
    score: float
    original_data: Optional[str] = None
    content_text: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    ocr_text: str = ""
    used_contexts: List[ContextDocument] = Field(default_factory=list)

class HealthStatusResponse(BaseModel):
    db_ok: bool
    ollama_ok: bool
    gemini_ok: bool
    ocr_ok: bool

class DocumentCountResponse(BaseModel):
    total: int
    per_table: Dict[str, int]
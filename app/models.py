from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

# Request/Response Models
class QueryRequest(BaseModel):
    query_text: str = Field(..., description="Text query for RAG system")
    top_k: Optional[int] = Field(5, description="Number of results to return")
    table_name: Optional[str] = Field("documents", description="Table to query")
    
class ImageQueryRequest(BaseModel):
    query_text: Optional[str] = Field(None, description="Optional text query")
    top_k: Optional[int] = 5
    table_name: Optional[str] = "documents"

class QueryResponse(BaseModel):
    answer: str = Field(..., description="AI generated answer")
    sources: List[str] = Field(..., description="Source documents used")
    similarity_scores: List[float] = Field(..., description="Similarity scores")
    query_time: float = Field(..., description="Query processing time in seconds")
    
class HealthStatusResponse(BaseModel):
    database_status: str = Field(..., description="PostgreSQL connection status")
    ollama_status: str = Field(..., description="Ollama service status")
    embedding_model_status: str = Field(..., description="Embedding model status")
    chat_model_status: str = Field(..., description="Chat model status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    
class DocumentCountResponse(BaseModel):
    table_name: str = Field(..., description="Table name")
    count: int = Field(..., description="Number of documents")
    timestamp: datetime = Field(..., description="Count timestamp")
    
# Database Models
class Document(BaseModel):
    id: int
    original_data: dict
    content_text: str
    embedding: List[float]
    created_at: datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
from typing import Optional

from app.models import (
    QueryRequest, QueryResponse, 
    HealthStatusResponse, DocumentCountResponse,
    ImageQueryRequest
)
from app.rag import rag_system
from app.database import vector_db
from app.ocr import ocr_processor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RAG Chatbot Service",
    description="Retrieval-Augmented Generation Chatbot with Vector Database",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RAG Router
@app.post("/api/rag/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Query the RAG system with a text query
    
    - **query_text**: Text query for the RAG system
    - **top_k**: Number of similar documents to retrieve (default: 5)
    - **table_name**: Table to search in (default: "documents")
    """
    try:
        result = rag_system.query_rag(
            query_text=request.query_text,
            table_name=request.table_name,
            top_k=request.top_k
        )
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/query-with-image")
async def query_rag_with_image(
    query_text: Optional[str] = Form(None),
    image: UploadFile = File(...),
    top_k: int = Form(5),
    table_name: str = Form("documents")
):
    """
    Query the RAG system with an image (and optional text)
    
    - **image**: Image file (JPEG, PNG, etc.)
    - **query_text**: Optional text query
    - **top_k**: Number of similar documents to retrieve
    - **table_name**: Table to search in
    """
    try:
        # Read image bytes
        image_bytes = await image.read()
        
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Image file is empty")
        
        # Process with RAG
        result = rag_system.query_with_image(
            image_bytes=image_bytes,
            query_text=query_text,
            table_name=table_name,
            top_k=top_k
        )
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Image query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rag/health", response_model=HealthStatusResponse)
async def health_check():
    """
    Get health status of the RAG system components
    
    Checks:
    - PostgreSQL database connection
    - Ollama service
    - Embedding model availability
    - Chat model availability
    """
    try:
        # Check database
        db_healthy = vector_db.health_check()
        
        # Check Ollama
        ollama_health = rag_system.check_ollama_health()
        
        return HealthStatusResponse(
            database_status="healthy" if db_healthy else "unhealthy",
            ollama_status="healthy" if ollama_health["ollama"] else "unhealthy",
            embedding_model_status="available" if ollama_health["embedding_model"] else "unavailable",
            chat_model_status="available" if ollama_health["chat_model"] else "unavailable",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rag/documents/count", response_model=DocumentCountResponse)
async def get_document_count(table_name: str = "documents"):
    """
    Get the total number of documents in the vector store
    
    - **table_name**: Table to count documents from (default: "documents")
    """
    try:
        count = vector_db.get_document_count(table_name)
        
        return DocumentCountResponse(
            table_name=table_name,
            count=count,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Document count failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "RAG Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/api/rag/health",
            "query": "/api/rag/query",
            "query_with_image": "/api/rag/query-with-image",
            "document_count": "/api/rag/documents/count"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
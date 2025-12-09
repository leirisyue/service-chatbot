import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.rag import rag_router
from app.config import settings

app = FastAPI(
    title="RAG Chatbot Service",
    version="0.1.0",
    description="Service Chatbot cho mô hình RAG: OCR ảnh, embedding với Ollama, truy vấn Postgres và trả lời bằng Gemini."
)

# CORS (tùy chỉnh theo nhu cầu)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(rag_router, tags=["RAG"])

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_RELOAD,
    )
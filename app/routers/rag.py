from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from app.schemas import QueryResponse, HealthStatusResponse, DocumentCountResponse, ContextDocument
from app.ocr import ocr_images_to_text, health_check_ocr
from app.embedding import embed_text, health_check_ollama
from app.db import health_check_db, similarity_search_across_tables, count_documents_per_table
from app.llm import generate_answer, health_check_gemini
from app.config import settings
from PIL import Image
from io import BytesIO

rag_router = APIRouter()

@rag_router.post("/query", response_model=QueryResponse, summary="Query the RAG system with a text query")
async def query_rag(
    text: Optional[str] = Form(default=None, description="Câu hỏi/đoạn văn bản"),
    top_k: int = Form(default=settings.APP_TOP_K, ge=1, le=50),
    min_score: float = Form(default=settings.APP_MIN_SCORE, ge=0.0, le=1.0),
):
    print("start /query")
    # Collect images bytes
    image_bytes_list: List[bytes] = []
    # pil_images: List[Image] = []
    # if files:
    #     for f in files:
    #         content = await f.read()
    #         if content:
    #             image_bytes_list.append(content)
    #             try:
    #                 pil_images.append(Image.open(BytesIO(content)).convert("RGB"))
    #             except Exception:
    #                 pass

    print("text input",text)
    ocr_text = ocr_images_to_text(image_bytes_list) if image_bytes_list else ""
    user_text = (text or "").strip()
    merged_text = " ".join([t for t in [user_text, ocr_text] if t]).strip()

    
    if not merged_text:
        raise HTTPException(status_code=400, detail="Thiếu input: cần cung cấp text hoặc ít nhất một ảnh chứa chữ.")

    # Embed merged text
    query_vec = embed_text(merged_text)

    # Vector search
    hits = similarity_search_across_tables(query_vec, top_k=top_k, min_score=min_score)

    # Build contexts for LLM
    context_strings: List[str] = []
    used_contexts: List[ContextDocument] = []
    for h in hits:
        ctx_line = f"[{h['table']}#{h['id']} score={h['score']:.3f}]\noriginal_data: {h.get('original_data')}\ncontent_text: {h.get('content_text')}"
        context_strings.append(ctx_line)
        used_contexts.append(ContextDocument(
            table=h["table"],
            id=h["id"],
            score=float(h["score"] or 0.0),
            original_data=h.get("original_data"),
            content_text=h.get("content_text"),
        ))

    # LLM answer (pass original images too)
    answer = generate_answer(user_text or merged_text, context_strings)

    return QueryResponse(answer=answer, ocr_text=ocr_text, used_contexts=used_contexts)

@rag_router.get("/health", response_model=HealthStatusResponse, summary="Get health status of the RAG system components.")
async def health():
    return HealthStatusResponse(
        db_ok=health_check_db(),
        ollama_ok=health_check_ollama(),
        gemini_ok=health_check_gemini(),
        ocr_ok=health_check_ocr(),
    )

@rag_router.get("/documents/count", response_model=DocumentCountResponse, summary="Get the total number of documents in the vector store.")
async def documents_count():
    per_table = count_documents_per_table()
    return DocumentCountResponse(total=sum(per_table.values()), per_table=per_table)
# RAG Chatbot Service

Service Chatbot cho mô hình RAG:
- Nhận text + ảnh (ảnh sẽ OCR trước), tạo embedding bằng Ollama, truy vấn PostgreSQL (các bảng có cột `embedding`), và trả lời bằng Gemini.
- Bỏ qua service vector (indexing/chunking); Service này chỉ làm phần Query + Chat.

## Kiến trúc nhanh
- OCR: Tesseract (pytesseract)
- Embedding: Ollama `nomic-embed-text:latest` qua REST (`/api/embeddings`)
- Vector DB: PostgreSQL + pgvector. Các bảng phải có cấu trúc:
  ```
  id | original_data | content_text | embedding | created_at
  ```
- LLM: Gemini (Google AI Studio) — model mặc định `gemini-1.5-pro`
- API: FastAPI
- Swagger UI: http://localhost:8000/docs

## Biến môi trường

Tạo file `.env` từ `.env.example` và chỉnh sửa:

```
APP_PG_HOST=host.docker.internal
APP_PG_USER=postgres
APP_PG_PASSWORD=postgres
APP_PG_DATABASE=ultimate_advisor
APP_PG_PORT=5432

# Ollama
OLLAMA_HOST=http://host.docker.internal:11434
APP_EMBEDDING_MODEL=nomic-embed-text:latest

# Gemini
GOOGLE_API_KEY=your_google_ai_studio_key
APP_GEMINI_MODEL=gemini-1.5-pro

# App
APP_RELOAD=false
APP_TOP_K=5
APP_MIN_SCORE=0.3
```

Lưu ý:
- `host.docker.internal` cho phép container truy cập dịch vụ chạy trên host (PostgreSQL, Ollama). Với Linux, Docker Desktop hỗ trợ `host-gateway` trong `docker-compose.yml` (đã cấu hình).
- Đảm bảo Postgres đã cài extension `pgvector`:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```

## Chạy project

```bash
docker compose up --build
```

- Swagger: http://localhost:8000/docs
- Health: `GET /health`
- Query: `POST /query` (multipart/form-data: `text` + `files[]`)

## API

- `POST /query`
  - Form fields:
    - `text`: string (optional)
    - `top_k`: int (optional, default theo env)
    - `min_score`: float 0..1 (optional)
    - `files`: list file ảnh (optional)
  - Trả về:
    - `answer`: câu trả lời từ Gemini
    - `ocr_text`: text OCR được từ ảnh
    - `used_contexts[]`: các context đã dùng (bảng, id, score, original_data, content_text)

- `GET /health`
  - Kiểm tra DB, Ollama, Gemini, OCR

- `GET /documents/count`
  - Đếm tổng số document (embedding không null) trên tất cả các bảng có cột `embedding`

## Ghi chú kỹ thuật
- Truy vấn similarity: mỗi bảng top-k theo cosine distance (`<=>`) nếu có; nếu không có thì fallback Euclidean (`<->`) và chuẩn hóa.
- Hợp nhất kết quả và sắp xếp toàn cục (global top-k).
- OCR dùng `tesseract-ocr` + gói ngôn ngữ Việt (`tesseract-ocr-vie`). Có thể thêm ngôn ngữ khác nếu cần.
- Prompt LLM có kèm CONTEXT và (nếu có) cả ảnh gốc để Gemini hiểu thêm.

## Mở rộng
- Bổ sung chấm điểm nguồn, trích dẫn.
- Bộ nhớ hội thoại (conversation memory).
- Cache embedding và/hoặc kết quả truy vấn.
import os
import time
import json
import logging
from typing import List, Tuple, Any, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import google.generativeai as genai
import requests

try:
    import tiktoken
except ImportError:
    tiktoken = None


# =========================
# 1. Load environment
# =========================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "models/text-embedding-004")

QWEN_EMBED_MODEL = os.getenv("QWEN_EMBED_MODEL", "qwen3-embedding:latest")
QWEN_API_BASE = os.getenv("QWEN_API_BASE", "http://localhost:11434")  # ví dụ Ollama

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
PG_DATABASE = os.getenv("PG_DATABASE", "postgres")

# Kiểu lưu embedding trong DB: "vector" (pgvector) hoặc "jsonb"
EMBEDDING_STORAGE_TYPE = os.getenv("EMBEDDING_STORAGE_TYPE", "vector").lower()


# =========================
# 2. Logging setup
# =========================

def setup_logging(log_dir: str = "logs") -> str:
    os.makedirs(log_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"embed_test_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler()
        ],
    )
    logging.info(f"Logging to {log_path}")
    return log_path


# =========================
# 3. Helper: make JSON-safe
# =========================

def to_jsonable(obj):
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    elif hasattr(obj, "isoformat"):
        try:
            return obj.isoformat()
        except Exception:
            return str(obj)
    else:
        try:
            json.dumps(obj)
            return obj
        except TypeError:
            return str(obj)


# =========================
# 4. Helper: token counting
# =========================
def estimate_tokens(texts: List[str], model_name: str = "gpt-4o-mini") -> int:
    if not texts:
        return 0

    if tiktoken is None:
        return sum(len(t.split()) for t in texts)

    try:
        enc = tiktoken.encoding_for_model(model_name)
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")

    total = 0
    for t in texts:
        total += len(enc.encode(t))
    return total


# =========================
# 5. Postgres helpers
# =========================

def get_pg_connection():
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        dbname=PG_DATABASE,
    )
    return conn


def ensure_embedding_tables():
    """
    Tạo bảng gemini_embeddings & qwen_embeddings nếu chưa có.
    Hỗ trợ 2 kiểu:
      - vector (pgvector, embedding VECTOR)
      - jsonb (embedding JSONB)
    """
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            if EMBEDDING_STORAGE_TYPE == "vector":
                # cần extension vector
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS gemini_embeddings (
                        id SERIAL PRIMARY KEY,
                        source_table TEXT NOT NULL,
                        source_pk TEXT,
                        row_index INT NOT NULL,
                        text TEXT NOT NULL,
                        embedding VECTOR,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS qwen_embeddings (
                        id SERIAL PRIMARY KEY,
                        source_table TEXT NOT NULL,
                        source_pk TEXT,
                        row_index INT NOT NULL,
                        text TEXT NOT NULL,
                        embedding VECTOR,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    """
                )
            else:
                # lưu dạng JSONB
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS gemini_embeddings (
                        id SERIAL PRIMARY KEY,
                        source_table TEXT NOT NULL,
                        source_pk TEXT,
                        row_index INT NOT NULL,
                        text TEXT NOT NULL,
                        embedding JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS qwen_embeddings (
                        id SERIAL PRIMARY KEY,
                        source_table TEXT NOT NULL,
                        source_pk TEXT,
                        row_index INT NOT NULL,
                        text TEXT NOT NULL,
                        embedding JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    """
                )
        conn.commit()
    finally:
        conn.close()


def insert_embedding_rows(
    model: str,
    table_name: str,
    texts: List[str],
    raw_rows: List[Any],
    embeddings: List[List[float]],
):
    """
    Lưu embedding vào bảng:
      - model = "gemini" -> gemini_embeddings
      - model = "qwen"   -> qwen_embeddings
    """
    if not embeddings:
        logging.info(f"No embeddings to insert for model={model}")
        return

    if model not in ("gemini", "qwen"):
        raise ValueError("model must be 'gemini' or 'qwen'")

    target_table = "gemini_embeddings" if model == "gemini" else "qwen_embeddings"

    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            for idx, (text, row, emb) in enumerate(zip(texts, raw_rows, embeddings)):
                # cố gắng lấy khóa chính 'id' từ row nếu có
                source_pk: Optional[str] = None
                if isinstance(row, dict):
                    if "id" in row:
                        source_pk = str(row["id"])
                    elif "ID" in row:
                        source_pk = str(row["ID"])

                if EMBEDDING_STORAGE_TYPE == "vector":
                    # chèn dạng ARRAY -> VECTOR (pgvector)
                    # cú pháp: embedding = %s::vector
                    emb_str = "[" + ",".join(str(float(x)) for x in emb) + "]"
                    sql = f"""
                        INSERT INTO {target_table} (source_table, source_pk, row_index, text, embedding)
                        VALUES (%s, %s, %s, %s, %s::vector)
                    """
                    params = (table_name, source_pk, idx, text, emb_str)
                else:
                    # lưu JSONB
                    sql = f"""
                        INSERT INTO {target_table} (source_table, source_pk, row_index, text, embedding)
                        VALUES (%s, %s, %s, %s, %s::jsonb)
                    """
                    params = (table_name, source_pk, idx, text, json.dumps(emb))

                cur.execute(sql, params)

        conn.commit()
        logging.info(
            f"Inserted {len(embeddings)} rows into {target_table} "
            f"(storage_type={EMBEDDING_STORAGE_TYPE})"
        )
    finally:
        conn.close()


def fetch_rows_from_table(
    table_name: str,
    limit: int = 1000,
) -> Tuple[List[str], List[Any]]:
    conn = get_pg_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = f"SELECT * FROM public.\"{table_name}\" LIMIT %s;"
            logging.info(f"Executing query: {query} with limit={limit}")
            cur.execute(query, (limit,))
            rows = cur.fetchall()

            texts = []
            for row in rows:
                parts = []
                for col, val in row.items():
                    if val is None:
                        v_str = ""
                    else:
                        v_str = str(val)
                    parts.append(f"{col}={v_str}")
                row_text = " | ".join(parts)
                texts.append(row_text)

        logging.info(f"Fetched {len(texts)} rows from table '{table_name}'.")
        return texts, rows
    finally:
        conn.close()


# =========================
# 6. Gemini embedding + logging + DB save
# =========================
def embed_with_gemini(
    table_name: str,
    texts: List[str],
    raw_rows: List[Any],
    output_dir: str,
) -> Tuple[List[List[float]], float, int, str]:
    if not texts:
        return [], 0.0, 0, ""

    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    outfile = os.path.join(
        output_dir,
        f"{table_name}_gemini_embeddings_{timestamp}.jsonl"
    )

    genai.configure(api_key=GEMINI_API_KEY)

    embeddings: List[List[float]] = []
    start = time.time()
    with open(outfile, "w", encoding="utf-8") as f:
        for idx, (t, row) in enumerate(zip(texts, raw_rows)):
            resp = genai.embed_content(
                model=GEMINI_EMBED_MODEL,
                content=t,
            )
            emb = resp["embedding"] if isinstance(resp, dict) else resp.embedding
            embeddings.append(emb)

            record = {
                "row_index": idx,
                "text": t,
                "raw_row": to_jsonable(row),
                "embedding": to_jsonable(emb),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    elapsed = time.time() - start
    token_est = estimate_tokens(texts)

    logging.info(
        f"Gemini embeddings done: {len(embeddings)} rows, "
        f"time={elapsed:.2f}s, tokens≈{token_est}, output={outfile}"
    )

    # Lưu vào DB
    insert_embedding_rows("gemini", table_name, texts, raw_rows, embeddings)

    return embeddings, elapsed, token_est, outfile


# =========================
# 7. Qwen embedding + logging + DB save
# =========================
def embed_with_qwen(
    table_name: str,
    texts: List[str],
    raw_rows: List[Any],
    output_dir: str,
) -> Tuple[List[List[float]], float, int, str]:
    if not texts:
        return [], 0.0, 0, ""

    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    outfile = os.path.join(
        output_dir,
        f"{table_name}_qwen_embeddings_{timestamp}.jsonl"
    )

    url = f"{QWEN_API_BASE}/api/embeddings"
    embeddings: List[List[float]] = []
    start = time.time()
    with open(outfile, "w", encoding="utf-8") as f:
        for idx, (t, row) in enumerate(zip(texts, raw_rows)):
            payload = {
                "model": QWEN_EMBED_MODEL,
                "prompt": t,
            }
            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            emb = data.get("embedding") or data.get("data", [{}])[0].get("embedding")
            if emb is None:
                raise ValueError(f"Qwen API response không có 'embedding': {data}")
            embeddings.append(emb)

            record = {
                "row_index": idx,
                "text": t,
                "raw_row": to_jsonable(row),
                "embedding": to_jsonable(emb),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    elapsed = time.time() - start
    token_est = estimate_tokens(texts)

    logging.info(
        f"Qwen embeddings done: {len(embeddings)} rows, "
        f"time={elapsed:.2f}s, tokens≈{token_est}, output={outfile}"
    )

    # Lưu vào DB
    insert_embedding_rows("qwen", table_name, texts, raw_rows, embeddings)

    return embeddings, elapsed, token_est, outfile


# =========================
# 8. Main test
# =========================
def run_test(table_name: str, limit: int = 1000):
    logging.info(f"Starting test for table='{table_name}', limit={limit}")

    # Đảm bảo 2 bảng embedding tồn tại
    ensure_embedding_tables()

    texts, raw_rows = fetch_rows_from_table(table_name, limit=limit)
    logging.info(f"Got {len(texts)} rows to embed.")

    output_dir = "embeddings_output"
    os.makedirs(output_dir, exist_ok=True)

    # Test Gemini
    logging.info("=== Start Gemini embedding ===")
    gem_embs, gem_time, gem_tokens, gem_file = embed_with_gemini(
        table_name, texts, raw_rows, output_dir
    )
    logging.info(f"Gemini - vectors: {len(gem_embs)}, time={gem_time:.2f}s, tokens≈{gem_tokens}")

    # Test Qwen
    logging.info("=== Start Qwen embedding ===")
    qwen_embs, qwen_time, qwen_tokens, qwen_file = embed_with_qwen(
        table_name, texts, raw_rows, output_dir
    )
    logging.info(f"Qwen  - vectors: {len(qwen_embs)}, time={qwen_time:.2f}s, tokens≈{qwen_tokens}")

    # So sánh sơ bộ
    logging.info("=== Summary ===")
    logging.info(f"Rows: {len(texts)}")
    logging.info(f"Gemini: time={gem_time:.2f}s, tokens≈{gem_tokens}, file={gem_file}")
    logging.info(f"Qwen : time={qwen_time:.2f}s, tokens≈{qwen_tokens}, file={qwen_file}")

    print("\n=== Summary ===")
    print(f"Rows: {len(texts)}")
    print(f"Gemini: time={gem_time:.2f}s, tokens≈{gem_tokens}, file={gem_file}")
    print(f"Qwen : time={qwen_time:.2f}s, tokens≈{qwen_tokens}, file={qwen_file}")


if __name__ == "__main__":
    import argparse

    log_file = setup_logging()

    parser = argparse.ArgumentParser(
        description="Test embedding từ Postgres table bằng Gemini & Qwen, có log, file JSONL và lưu DB"
    )
    parser.add_argument("--table", required=True, help="Tên bảng trong Postgres")
    parser.add_argument("--limit", type=int, default=1000, help="Số dòng tối đa")
    args = parser.parse_args()

    run_test(args.table, args.limit)
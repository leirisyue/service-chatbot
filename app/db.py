from typing import List, Tuple, Dict, Any, Optional
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector
from app.config import settings
from .logger import setup_logger
logger = setup_logger(__name__)

dsn = (
    f"host={settings.APP_PG_HOST} "
    f"port={settings.APP_PG_PORT} "
    f"dbname={settings.APP_PG_DATABASE} "
    f"user={settings.APP_PG_USER} "
    f"password={settings.APP_PG_PASSWORD}"
)

def _on_connect(conn):
    try:
        register_vector(conn)
    except Exception:
        pass

pool = ConnectionPool(conninfo=dsn, kwargs={"row_factory": dict_row}, open=_on_connect)

pool.wait()

def health_check_db() -> bool:
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        return True
    except Exception:
        return False

def list_embedding_tables() -> List[Tuple[str, str]]:
    q = """
    SELECT c.table_schema, c.table_name
    FROM information_schema.columns c
    JOIN information_schema.columns c2 ON c2.table_schema=c.table_schema AND c2.table_name=c.table_name AND c2.column_name='id'
    JOIN information_schema.columns c3 ON c3.table_schema=c.table_schema AND c3.table_name=c.table_name AND c3.column_name='original_data'
    JOIN information_schema.columns c4 ON c4.table_schema=c.table_schema AND c4.table_name=c.table_name AND c4.column_name='content_text'
    WHERE c.column_name='embedding' 
      AND c.table_schema NOT IN ('pg_catalog','information_schema');
    """
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(q)
        rows = cur.fetchall()
    return [(r["table_schema"], r["table_name"]) for r in rows]

def count_documents_per_table() -> Dict[str, int]:
    tables = list_embedding_tables()
    result: Dict[str, int] = {}
    with pool.connection() as conn, conn.cursor() as cur:
        for schema, table in tables:
            cur.execute(f'SELECT COUNT(*) AS c FROM "{schema}"."{table}" WHERE embedding IS NOT NULL;')
            c = cur.fetchone()["c"]
            result[f"{schema}.{table}"] = int(c)
    return result

def get_embedding_dimension(schema: str, table: str) -> Optional[int]:
    """
    Lấy chiều của cột vector 'embedding' bằng cách đọc một bản ghi đầu tiên.
    Nếu không có dữ liệu, trả None.
    """
    with pool.connection() as conn, conn.cursor() as cur:
        try:
            cur.execute(f'SELECT embedding FROM "{schema}"."{table}" WHERE embedding IS NOT NULL LIMIT 1;')
            row = cur.fetchone()
            if not row or row.get("embedding") is None:
                return None
            emb = row["embedding"]
            if isinstance(emb, (list, tuple)):
                return len(emb)
            # Một số adapter có thể trả Vector object
            try:
                return len(list(emb))
            except Exception:
                return None
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return None

def _table_topk(schema: str, table: str, query_vec: List[float], top_k: int) -> List[Dict[str, Any]]:
    """
    Lấy top_k từ 1 bảng theo cosine distance (<=>). Nếu lỗi, fallback Euclidean (<->).
    Truyền list/tuple làm tham số vector (pgvector adapter hỗ trợ trực tiếp).
    """
    with pool.connection() as conn, conn.cursor() as cur:
        param_vec = query_vec  # adapter pgvector/psycopg chấp nhận list/tuple
        try:
            sql = f'''
                SELECT 
                    id, original_data, content_text, 
                    (1 - (embedding <=> %s))::double precision AS score
                FROM "{schema}"."{table}"
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s
                LIMIT %s;
            '''
            cur.execute(sql, (param_vec, param_vec, top_k))
            return cur.fetchall()
        except Exception as e:
            logger.warning("Cosine query failed on %s.%s: %s. Falling back to Euclidean.", schema, table, e)
            try:
                conn.rollback()
            except Exception:
                pass
            sql = f'''
                SELECT 
                    id, original_data, content_text, 
                    (1.0 / (1.0 + (embedding <-> %s)))::double precision AS score
                FROM "{schema}"."{table}"
                WHERE embedding IS NOT NULL
                ORDER BY embedding <-> %s
                LIMIT %s;
            '''
            cur.execute(sql, (param_vec, param_vec, top_k))
            return cur.fetchall()

def similarity_search_table(schema: str, table: str, query_vec: List[float], top_k: int, min_score: float) -> List[Dict[str, Any]]:
    rows = _table_topk(schema, table, query_vec, top_k)
    out: List[Dict[str, Any]] = []
    for r in rows:
        r_out = dict(r)
        r_out["table"] = f"{schema}.{table}"
        out.append(r_out)
    out.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return [r for r in out if (r.get("score") or 0.0) >= min_score]
from typing import List, Tuple, Dict, Any
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector
from app.config import settings

dsn = (
    f"host={settings.APP_PG_HOST} "
    f"port={settings.APP_PG_PORT} "
    f"dbname={settings.APP_PG_DATABASE} "
    f"user={settings.APP_PG_USER} "
    f"password={settings.APP_PG_PASSWORD}"
)

pool = ConnectionPool(conninfo=dsn, kwargs={"row_factory": dict_row})

# Register pgvector when a connection is created
def _on_connect(conn):
    try:
        register_vector(conn)
    except Exception:
        pass

pool.wait()  # ensure pool is ready
with pool.connection() as conn:
    _on_connect(conn)

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
    """
    Trả về danh sách (schema, table) có cột 'embedding' và các cột chuẩn id|original_data|content_text|embedding
    """
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

def _table_topk(schema: str, table: str, query_vec: list, top_k: int) -> List[Dict[str, Any]]:
    """
    Lấy top_k từ 1 bảng theo cosine distance (<=>). Nếu không có, fallback Euclidean (<->).
    Trả về dict có score trong [0,1] (1 - cosine_distance).
    """
    with pool.connection() as conn, conn.cursor() as cur:
        # Try cosine distance
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
            cur.execute(sql, (query_vec, query_vec, top_k))
            return cur.fetchall()
        except Exception:
            # Fallback Euclidean distance normalized (rough heuristic): score = 1 / (1 + distance)
            sql = f'''
                SELECT 
                    id, original_data, content_text, 
                    (1.0 / (1.0 + (embedding <-> %s)))::double precision AS score
                FROM "{schema}"."{table}"
                WHERE embedding IS NOT NULL
                ORDER BY embedding <-> %s
                LIMIT %s;
            '''
            cur.execute(sql, (query_vec, query_vec, top_k))
            return cur.fetchall()

def similarity_search_across_tables(query_vec: list, top_k: int, min_score: float) -> List[Dict[str, Any]]:
    print('query_vec',query_vec)
    tables = list_embedding_tables()
    print('Searching in tables:', tables)
    
    all_rows: List[Dict[str, Any]] = []
    for schema, table in tables:
        rows = _table_topk(schema, table, query_vec, top_k)
        for r in rows:
            r_out = dict(r)
            r_out["table"] = f"{schema}.{table}"
            all_rows.append(r_out)
    # sort and top_k globally
    all_rows.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    filtered = [r for r in all_rows if (r.get("score") or 0.0) >= min_score]
    return filtered[:top_k]
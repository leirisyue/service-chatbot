import psycopg2
import pandas as pd
from config import settings
from logger import logger

def load_table_as_text(table_name: str, limit: int = 1000):
    logger.info(f"Connecting to Postgres DB: {settings.POSTGRES_DB}")
    logger.info(f"Reading table: {table_name}, limit={limit}")

    conn = psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD
    )

    query = f'SELECT * FROM "{table_name}" LIMIT {limit}'
    df = pd.read_sql(query, conn)
    conn.close()

    logger.info(f"Fetched {len(df)} rows from table {table_name}")

    texts = []
    row_ids = []

    for idx, row in df.iterrows():
        parts = []

        for col, val in row.items():
            if val is None:
                continue
            parts.append(f"{col}: {val}")

        text = "\n".join(parts)

        texts.append(text)
        row_ids.append(row.get("id"))

        logger.info(
            f"[ROW {idx}] row_id={row.get('id')} | text_length={len(text)}"
        )

    logger.info("Finished converting rows to embedding text")
    return texts, row_ids

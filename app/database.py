import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class VectorDatabase:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Establish connection to PostgreSQL"""
        try:
            self.connection = psycopg2.connect(
                host=settings.APP_PG_HOST,
                user=settings.APP_PG_USER,
                password=settings.APP_PG_PASSWORD,
                database=settings.APP_PG_DATABASE,
                port=settings.APP_PG_PORT
            )
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def get_connection(self):
        """Get database connection"""
        if self.connection is None or self.connection.closed:
            self.connect()
        return self.connection
    
    def similarity_search(self, query_embedding: List[float], 
                        table_name: str = "documents",
                        top_k: int = 5,
                        threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar vectors using cosine similarity
        """
        conn = self.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Convert list to string for PostgreSQL array
            embedding_array = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # Sử dụng định dạng an toàn cho tên bảng
            # Lưu ý: Tên bảng không thể parameterized trong PostgreSQL
            query = f"""
            SELECT id, original_data, content_text, created_at,
                   1 - (embedding <=> '{embedding_array}'::vector) as similarity
            FROM {table_name}
            WHERE 1 - (embedding <=> '{embedding_array}'::vector) > {threshold}
            ORDER BY embedding <=> '{embedding_array}'::vector
            LIMIT {top_k};
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Convert RealDictRow to regular dict
            return [dict(row) for row in results]
    
    def get_document_count(self, table_name: str = "documents") -> int:
        """Get total document count from a table"""
        conn = self.get_connection()
        with conn.cursor() as cursor:
            query = f"SELECT COUNT(*) FROM {table_name};"
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def health_check(self) -> bool:
        """Check database connection health"""
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()

# Singleton instance
vector_db = VectorDatabase()
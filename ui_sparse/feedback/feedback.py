
import json
from datetime import datetime
from typing import Dict, List, Optional

import psycopg2
from config import settings
from fastapi import APIRouter, HTTPException, Request
from psycopg2.extras import RealDictCursor
from chatapi.unit import FeedbackRequest
from chatapi.embeddingapi import generate_sparse_embedding

def get_db():
    return psycopg2.connect(**settings.DB_CONFIG)

router = APIRouter()
# ========================================
# FUNCTION DEFINITIONS
# ========================================

def save_user_feedback(session_id: str, query: str, selected_items: list, rejected_items: list, search_type: str):
    """
    Lưu phản hồi của user về kết quả tìm kiếm
    
    Args:
        session_id: ID session
        query: Câu hỏi gốc
        selected_items: List các item user chọn là ĐÚNG (headcode hoặc id_sap)
        rejected_items: List các item user bỏ qua/từ chối
        search_type: "product" hoặc "material"
    """
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # TẠO EMBEDDING CHO QUERY NGAY KHI LƯU
        query_embedding = generate_sparse_embedding(query)
        
        if not query_embedding:
            print("WARNING: Không tạo được embedding, vẫn lưu feedback")
        
        sql = """
            INSERT INTO user_feedback 
            (session_id, query, selected_items, rejected_items, search_type, query_embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        cur.execute(sql, (
            session_id,
            query,
            json.dumps(selected_items),
            json.dumps(rejected_items),
            search_type,
            query_embedding 
        ))
        
        feedback_id = cur.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        print(f"Feedback saved: {len(selected_items)} selected, {len(rejected_items)} rejected")
        print(f"   → Feedback ID: {feedback_id}")
        print(f"   → Embedding: {'OK' if query_embedding else 'ERROR NULL'}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to save feedback: {e}")
        import traceback
        traceback.print_exc()
        return False

# ========================================
# API ENDPOINTS
# ========================================

@router.post("/feedback")
def submit_feedback(feedback: FeedbackRequest):
    """
    📝 Endpoint nhận feedback từ user về kết quả tìm kiếm
    """
    try:
        success = save_user_feedback(
            feedback.session_id,
            feedback.query,
            feedback.selected_items,
            feedback.rejected_items,
            feedback.search_type
        )
        
        if success:
            return {
                "message": "SUCCESS: Cảm ơn phản hồi của bạn! Kết quả tìm kiếm sẽ được cải thiện.",
                "saved": True
            }
        else:
            return {
                "message": "WARNING: Không thể lưu phản hồi",
                "saved": False
            }
            
    except Exception as e:
        return {
            "message": f"ERROR: {str(e)}",
            "saved": False
        }




from pydantic import BaseModel
from typing import Optional, List, Dict

# ========================================

class FeedbackRequest(BaseModel):
    session_id: str
    query: str
    selected_items: List[str]  # List of headcodes hoặc id_sap
    rejected_items: List[str] = []
    search_type: str  # "product" hoặc "material"

class ChatMessage(BaseModel):
    session_id: str
    message: str
    email: Optional[str] = None  # Make email optional for backward compatibility
    context: Optional[Dict] = {}


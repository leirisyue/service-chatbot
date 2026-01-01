
import json
from datetime import datetime
from typing import Dict, List, Optional

import psycopg2
from config import settings
from fastapi import APIRouter, HTTPException, Request
from psycopg2.extras import RealDictCursor
from chatapi.unit import FeedbackRequest
from chatapi.embeddingapi import generate_embedding_qwen

def get_db():
    return psycopg2.connect(**settings.DB_CONFIG)

router = APIRouter()
# ========================================
# FUNCTION DEFINITIONS
# ========================================

# ========================================
# API ENDPOINTS
# ========================================

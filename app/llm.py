from typing import List, Optional
import google.generativeai as genai
from PIL.Image import Image as PILImage
from app.config import settings

# Configure once
if settings.GOOGLE_API_KEY:
    genai.configure(api_key=settings.GOOGLE_API_KEY)

def health_check_gemini() -> bool:
    try:
        model = genai.GenerativeModel(settings.APP_GEMINI_MODEL)
        _ = model.generate_content("ping", generation_config={"max_output_tokens": 1})
        return True
    except Exception:
        return False

SYSTEM_PROMPT = (
    "Bạn là trợ lý AI cho hệ thống RAG. Trả lời ngắn gọn, đúng trọng tâm, bằng tiếng Việt khi có thể. "
    "Chỉ dựa vào CONTEXT cung cấp; nếu thiếu thông tin thì nói rõ là không chắc chắn."
)

def generate_answer(
    user_query: str,
    contexts: List[str],
    images: Optional[List[PILImage]] = None,
) -> str:
    """
    Gọi Gemini để sinh câu trả lời, truyền cả ảnh (nếu có).
    """
    parts: List = [SYSTEM_PROMPT]
    if contexts:
        ctx_joined = "\n\n---- CONTEXT ----\n" + "\n\n".join(contexts) + "\n-----------------\n"
        parts.append(ctx_joined)
    parts.append(f"Câu hỏi của người dùng: {user_query}")

    if images:
        # Append images to multimodal prompt
        parts.extend(images)

    model = genai.GenerativeModel(settings.APP_GEMINI_MODEL)
    resp = model.generate_content(parts, safety_settings=None)
    return (getattr(resp, "text", None) or "").strip() or "Xin lỗi, tôi chưa thể trả lời câu hỏi này."
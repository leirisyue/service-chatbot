import google.generativeai as genai
import time
from config import settings
from logger import logger

genai.configure(api_key=settings.GEMINI_API_KEY)

def embed_gemini(texts):
    vectors = []
    total_tokens = 0
    start = time.time()

    logger.info(f"Start Gemini embedding | rows={len(texts)}")

    for idx, t in enumerate(texts):
        logger.info(f"[Gemini] Embedding row {idx} | text_length={len(t)}")

        res = genai.embed_content(
            model=settings.GEMINI_EMBED_MODEL,
            content=t
        )

        vectors.append(res["embedding"])
        total_tokens += res.get("usage", {}).get("total_tokens", 0)

    elapsed = time.time() - start
    logger.info(
        f"Gemini embedding finished | time={elapsed:.2f}s | tokens={total_tokens}"
    )

    return vectors, total_tokens, elapsed

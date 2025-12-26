import ollama
import time
from config import settings
from logger import logger

def embed_qwen(texts):
    vectors = []
    total_tokens = 0
    start = time.time()

    logger.info(f"Start Qwen embedding | rows={len(texts)}")

    for idx, t in enumerate(texts):
        logger.info(f"[Qwen] Embedding row {idx} | text_length={len(t)}")

        res = ollama.embeddings(
            model=settings.QWEN_EMBED_MODEL,
            prompt=t
        )

        vectors.append(res["embedding"])
        total_tokens += res.get("prompt_eval_count", 0)

    elapsed = time.time() - start
    logger.info(
        f"Qwen embedding finished | time={elapsed:.2f}s | tokens={total_tokens}"
    )

    return vectors, total_tokens, elapsed

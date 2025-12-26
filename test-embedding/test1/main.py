from db import load_table_as_text
from embed_gemini import embed_gemini
from embed_qwen import embed_qwen
from metrics import retrieval_accuracy
from logger import logger

TABLE_NAME = "MD_Material_SAP"
LIMIT = 100

logger.info("===== START EMBEDDING TEST =====")

texts, row_ids = load_table_as_text(TABLE_NAME, LIMIT)

# Gemini
g_vecs, g_tokens, g_time = embed_gemini(texts)
g_acc = retrieval_accuracy(g_vecs)

# Qwen
q_vecs, q_tokens, q_time = embed_qwen(texts)
q_acc = retrieval_accuracy(q_vecs)

logger.info("===== RESULT =====")
logger.info(f"Table        : {TABLE_NAME}")
logger.info(f"Rows         : {len(texts)}")

logger.info("Gemini")
logger.info(f" Accuracy    : {g_acc:.4f}")
logger.info(f" Tokens      : {g_tokens}")
logger.info(f" Time (sec)  : {g_time:.2f}")

logger.info("Qwen")
logger.info(f" Accuracy    : {q_acc:.4f}")
logger.info(f" Tokens      : {q_tokens}")
logger.info(f" Time (sec)  : {q_time:.2f}")

logger.info("===== END =====")

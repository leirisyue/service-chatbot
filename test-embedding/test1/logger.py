import logging
import os
import sys
from datetime import datetime

LOG_DIR = "logs"
LOG_NAME = "embedding_test"

def setup_logger():
    # Tạo thư mục logs nếu chưa có
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(LOG_NAME)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # =========================
    # Console handler
    # =========================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # =========================
    # File handler
    # =========================
    log_file = os.path.join(
        LOG_DIR,
        f"{LOG_NAME}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    # Tránh add handler nhiều lần
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    logger.info(f"Logging to file: {log_file}")
    return logger


logger = setup_logger()
